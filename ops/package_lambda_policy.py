#!/usr/bin/env python3
"""
Package a Lambda function for Cloud Custodian

This script leverages Cloud Custodian code to dynamically create lambda archives
that include c7n, user-requested packages from mode.packages, and the handler code.
Config.json is generated from inputs.

Expects JSON input with:
- policies
- execution_options
- function_name
- role
- regions

Outputs information regarding the zips created in JSON format:
- package_versions
- zips: JSON map of region to zip path, hashes and tags
- condition_regions: JSON list of regions where policy would deploy based on conditions
"""

import copy
import hashlib
import json
import sys
from collections import defaultdict

from ops.common import (
    validate_policy_structure,
    return_result,
    return_error,
    validate_with_custodian,
    validate_policy_mode,
    ValidationError,
    hex_ascii_encoder,
    copy_archive,
    get_custodian_config,
    get_package_versions,
    get_regions,
    parse_policies,
    get_force_deploy_tags,
)

try:
    from c7n.mu import (
        custodian_archive,
        get_exec_options,
        PolicyHandlerTemplate,
    )
    from c7n.version import version
    from c7n.filters.core import OPERATORS, ValueFilter
except ImportError:  # pragma: no cover
    print("Cloud Custodian (c7n) package is not installed. Please install it", file=sys.stderr)
    sys.exit(1)


def get_archive(archive, policy_list, exec_options):
    """Add handler template and config to archive.

    Args:
        archive: PythonPackageArchive instance
        policy_list: List of one cloud custodian policy
        exec_options: Dict of execution-options

    Returns:
        PythonPackageArchive: Archive with handler and config added
    """
    try:
        config_data = {
            "execution-options": exec_options,
            "policies": policy_list,
        }
        archive.add_contents("config.json", json.dumps(config_data, indent=2))
    except AssertionError as e:
        raise RuntimeError(f"Failed to add config.json: {e}")

    try:
        archive.add_contents("custodian_policy.py", PolicyHandlerTemplate)
    except AssertionError as e:
        raise RuntimeError(f"Failed to add handler template: {e}")

    return archive


def create_custodian_archive(packages=None):
    """Create a Cloud Custodian lambda archive

    Args:
        packages: List of additional packages to include beyond c7n

    Returns:
        PythonPackageArchive: Archive object with c7n and specified packages
    """
    try:
        return custodian_archive(packages=packages)
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unexpected error creating custodian archive: {type(e).__name__}: {e}")


def process_lambda_package(query, processed_policy, condition_regions, exec_options, packages):
    """Process the lambda package creation.

    Regions whose expanded policy is identical share a single archive.

    Args:
        query: Query dictionary
        processed_policy: Dict of region to policy list
        condition_regions: Regions derived from the policy conditions
        exec_options: Dict of execution-options
        packages: List of packages to include

    Returns:
        dict: Result dictionary with information about the zip files

    Raises:
        Exception: If any step in the packaging process fails
    """
    groups = defaultdict(list)
    for region in sorted(processed_policy):
        content = json.dumps(processed_policy[region], sort_keys=True)
        groups[content].append(region)

    zips = {}
    for index, group_regions in enumerate(groups.values()):
        policy_list = processed_policy[group_regions[0]]

        archive = create_custodian_archive(packages=packages)
        archive = get_archive(archive, policy_list, exec_options)
        archive.close()

        try:
            base64_hash = archive.get_checksum()
            hex_hash = archive.get_checksum(encoder=hex_ascii_encoder, hasher=hashlib.sha256)
        except AssertionError as e:
            raise RuntimeError(f"Failed to calculate archive checksums: {e}")

        final_zip_path = copy_archive(archive, hex_hash, query["function_name"], clean=(index == 0))
        archive.remove()

        for region in group_regions:
            zips[region] = {
                "path": final_zip_path,
                "sha256_base64": base64_hash,
                "sha256_hex": hex_hash,
                "tags": policy_list[0].get("mode", {}).get("tags", {}),
            }

    # Include c7n with any additional packages and get versions
    try:
        all_packages = ["c7n"] + (packages if packages else [])
        package_versions = get_package_versions(all_packages)
    except Exception as e:  # pragma: no cover
        package_versions = {"error": f"Failed to get package versions: {e}"}

    return {
        "package_versions": json.dumps(package_versions),
        "condition_regions": json.dumps(condition_regions),
        "zips": json.dumps(zips),
    }


def process_exec_options(query):
    """Process a query that should contain execution_options

    Args:
        query: Dictionary with query parameters

    Returns:
        dictionary: containing valid execution options
    """
    try:
        exec_options_dict = json.loads(query["execution_options"])
        if not isinstance(exec_options_dict, dict):
            raise ValidationError("execution_options must be a JSON object/dictionary")
    except (json.JSONDecodeError, TypeError) as e:
        raise ValidationError(f"Could not parse 'execution_options' as JSON: {e}")

    for k in ("log_group", "tracer", "output_dir", "metrics_enabled"):
        if k not in exec_options_dict:
            exec_options_dict[k] = None
    return get_exec_options(exec_options_dict)


def get_condition_regions(policy_instance):
    """Return the regions matched by the region conditions in the policy

    Args:
        policy_instance: The validated Cloud Custodian policy instance

    Returns:
        list: Sorted list of regions matching the policy conditions
    """
    regions = set()

    if policy_contains_conditions(policy_instance):
        all_regions = get_regions()

        for filter_obj in policy_instance.conditions.iter_filters():
            if isinstance(filter_obj, ValueFilter):
                if hasattr(filter_obj, "data") and filter_obj.data.get("key") == "region":
                    op_name = filter_obj.data.get("op", "eq")
                    region_value = filter_obj.data.get("value", [])

                    op_func = OPERATORS[op_name]

                    for region in all_regions:
                        if op_func(region, region_value):
                            regions.add(region)

    return sorted(regions)


def policy_contains_conditions(policy_instance):
    return policy_instance.conditions is not None and list(
        policy_instance.conditions.iter_filters()
    )


def get_custodian_tags(policy_list, query):
    """Generate custodian-specific tags for a policy.

    Args:
        policy_list: List with one policy dict
        query: Dictionary with query parameters

    Returns:
        dict: Dictionary of custodian-specific tags
    """
    policy_dict = policy_list[0]
    mode = policy_dict["mode"]
    mode_type = mode["type"]
    tags = {"custodian-info": f"mode={mode_type}:version={version}"}

    if mode_type == "schedule":
        group = mode.get("group-name", "default")
        function_name = query["function_name"]
        tags["custodian-schedule"] = f"name={function_name}:group={group}"

    return tags


def get_tags(policy_list, query):
    """Generate all tags for a policy.

    Args:
        policy_list: List with one policy dict
        query: Dictionary with query parameters

    Returns:
        dict: Combined dictionary of all tags
    """
    tags = {}
    tags.update(get_custodian_tags(policy_list, query))
    tags.update(get_force_deploy_tags(query.get("force_deploy", "false").lower() == "true"))
    return tags


def add_tags_to_policy(policy_list, tags):
    """Add tags to policy mode tags.

    Args:
        policy_list: List of one cloud custodian policy
        tags: Dict of tags to add to the policy mode

    Returns:
        list: Policy list with tags added
    """
    if "tags" not in policy_list[0]["mode"]:
        policy_list[0]["mode"]["tags"] = {}

    policy_list[0]["mode"]["tags"].update(tags)

    return policy_list


def restore_output_dir(policy_data, unexpanded_data):
    """Restore output_dir, which Cloud Custodian resolves at runtime not at package time.

    Args:
        policy_data: Policy dict with variables expanded
        unexpanded_data: Copy of the policy dict taken before expansion

    Returns:
        dict: Policy dict with the original output_dir restored
    """
    original = unexpanded_data.get("mode", {}).get("execution-options", {})
    if "output_dir" in original:
        policy_data["mode"]["execution-options"]["output_dir"] = original["output_dir"]

    return policy_data


def expand_policy(policies_dict, query, region, account_id, tags):
    """Expand a policy's variables for a single region.

    Args:
        policies_dict: Dictionary containing the unexpanded policy data
        query: Dictionary with query parameters
        region: AWS region to expand the policy for
        account_id: Resolved AWS account id
        tags: Tags to add to the policy mode

    Returns:
        list: Policy list expanded for the given region
    """
    config = get_custodian_config(region=region, account_id=account_id)
    policy_instance = validate_with_custodian(copy.deepcopy(policies_dict), config)

    unexpanded_data = copy.deepcopy(policy_instance.data)
    policy_instance.expand_variables(policy_instance.get_variables())

    policy_list = add_tags_to_policy(
        [restore_output_dir(policy_instance.data, unexpanded_data)], tags
    )
    policy_list[0]["mode"]["role"] = query["role"]

    return policy_list


def get_requested_regions(query):
    """Determine the regions requested by the caller.

    Args:
        query: Dictionary with query parameters

    Returns:
        list: Sorted list of regions

    Raises:
        ValidationError: If regions cannot be parsed
    """
    try:
        regions = json.loads(query.get("regions") or "[]")
    except (json.JSONDecodeError, TypeError) as e:
        raise ValidationError(f"Could not parse 'regions' as JSON: {e}")

    return sorted(set(regions))


def process_policies(query):
    """Process a query that should contain policies.

    Args:
        query: Dictionary with query parameters

    Returns:
        tuple: (processed_policy, condition_regions, packages)
    """
    policies_dict = parse_policies(query)
    validate_policy_mode(validate_policy_structure(policies_dict)[0])

    policy_instance = validate_with_custodian(copy.deepcopy(policies_dict))
    packages = policy_instance.data.get("mode", {}).get("packages", [])
    tags = get_tags([policy_instance.data], query)

    requested_regions = get_requested_regions(query)
    condition_regions = []
    if not requested_regions:
        condition_regions = get_condition_regions(policy_instance)
    regions = requested_regions or condition_regions

    account_id = None
    if regions:
        account_id = get_custodian_config(region=regions[0]).account_id

    processed_policy = {
        region: expand_policy(policies_dict, query, region, account_id, tags) for region in regions
    }

    return processed_policy, condition_regions, packages


def main():
    try:
        query = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        return_error(f"Failed to parse input JSON: {e}")
    except Exception as e:  # pragma: no cover
        return_error(f"Unexpected error reading input: {type(e).__name__}: {e}")

    required = ["policies", "execution_options", "function_name", "role"]
    missing = [field for field in required if not query.get(field)]
    if missing:
        return_error(f"Missing required fields: {', '.join(missing)}")

    try:
        processed_policy, condition_regions, packages = process_policies(query)
    except ValidationError as e:
        return_error(str(e))

    try:
        exec_options = process_exec_options(query)
    except ValidationError as e:
        return_error(f"Failed to validate execution options: {e}")

    try:
        result = process_lambda_package(
            query, processed_policy, condition_regions, exec_options, packages
        )
        return_result(result)
    except RuntimeError as e:
        return_error(f"Failed to package lambda: {e}")


if __name__ == "__main__":
    main()  # pragma: no cover
