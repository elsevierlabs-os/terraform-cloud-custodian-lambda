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
- region

Outputs information regarding the zip created in JSON format:
- sha256_hex
- sha256_base64
- zip_path
- package_versions
- policy_regions: JSON list of regions where policy would deploy based on conditions
"""

import hashlib
import json
import sys

from ops.common import (
    validate_policy_structure,
    return_result,
    return_error,
    validate_with_custodian,
    validate_policy_mode,
    ValidationError,
    hex_ascii_encoder,
    copy_archive,
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


def add_handler_and_config_to_archive(archive, policy_list, exec_options):
    """Add handler template and config to archive.

    Args:
        archive: PythonPackageArchive instance
        policy_list: List of one cloud custodian policy
        exec_options: Dict of execution-options

    Returns:
        PythonPackageArchive: Archive with handler and config added
    """
    try:
        archive.add_contents("custodian_policy.py", PolicyHandlerTemplate)
    except AssertionError as e:
        raise RuntimeError(f"Failed to add handler template: {e}")

    try:
        config_data = {
            "execution-options": exec_options,
            "policies": policy_list,
        }
        archive.add_contents("config.json", json.dumps(config_data, indent=2))
    except AssertionError as e:
        raise RuntimeError(f"Failed to add config.json: {e}")

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


def process_lambda_package(query, policy_list, regions, exec_options, packages):
    """Process the lambda package creation.

    Args:
        query: Query dictionary
        policy_list: List with one policy
        exec_options: Dict of execution-options
        packages: List of packages to include
        validated_policy: Already validated Cloud Custodian Policy object

    Returns:
        dict: Result dictionary with information about the zip file

    Raises:
        Exception: If any step in the packaging process fails
    """
    archive = create_custodian_archive(packages=packages)
    archive = add_handler_and_config_to_archive(archive, policy_list, exec_options)
    archive.close()

    try:
        base64_hash = archive.get_checksum()
        hex_hash = archive.get_checksum(encoder=hex_ascii_encoder, hasher=hashlib.sha256)
    except AssertionError as e:
        raise RuntimeError(f"Failed to calculate archive checksums: {e}")

    final_zip_path = copy_archive(archive, hex_hash, query["function_name"])
    archive.remove()

    # Include c7n with any additional packages and get versions
    try:
        all_packages = ["c7n"] + (packages if packages else [])
        package_versions = get_package_versions(all_packages)
    except Exception as e:  # pragma: no cover
        package_versions = {"error": f"Failed to get package versions: {e}"}

    return {
        "sha256_hex": hex_hash,
        "sha256_base64": base64_hash,
        "zip_path": final_zip_path,
        "package_versions": json.dumps(package_versions),
        "custodian_tags": json.dumps(policy_list[0].get("mode", {}).get("tags", {})),
        "policy_regions": json.dumps(list(regions)),
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


def get_policy_regions(policy_instance):
    """Return policy region based cloud-custodian conditions in the policy

    Args:
        policy_instance: The validated Cloud Custodian policy instance

    Returns:
        tuple: (set of region values, set of condition types)
    """
    regions = set()

    all_regions = get_regions()

    if policy_contains_conditions(policy_instance):
        for filter_obj in policy_instance.conditions.iter_filters():
            if isinstance(filter_obj, ValueFilter):
                if hasattr(filter_obj, "data") and filter_obj.data.get("key") == "region":
                    op_name = filter_obj.data.get("op", "eq")
                    region_value = filter_obj.data.get("value", [])

                    op_func = OPERATORS[op_name]

                    for region in all_regions:
                        if op_func(region, region_value):
                            regions.add(region)

    return regions


def policy_contains_conditions(policy_instance):
    return policy_instance.conditions is not None and list(
        policy_instance.conditions.iter_filters()
    )


def get_custodian_tags(mode, policy_list):
    """Generate custodian-specific tags for a policy.

    Args:
        mode: The policy mode type
        policy_list: List with one policy dict

    Returns:
        dict: Dictionary of custodian-specific tags
    """
    tags = {"custodian-info": f"mode={mode}:version={version}"}
    
    # Add schedule tag for EventBridge Scheduler mode
    if mode == "schedule":
        policy = policy_list[0]
        prefix = policy.get("mode", {}).get("function-prefix", "custodian-")
        name = policy.get("name", "")
        group = policy.get("mode", {}).get("group-name", "default")
        tags["custodian-schedule"] = f"name={prefix}{name}:group={group}"
    
    return tags


def get_tags(mode, policy_list, force_deploy=False):
    """Generate all tags for a policy.

    Args:
        mode: The policy mode type
        policy_list: List with one policy dict
        force_deploy: Boolean indicating if force deployment is enabled

    Returns:
        dict: Combined dictionary of all tags
    """
    tags = {}
    tags.update(get_custodian_tags(mode, policy_list))
    tags.update(get_force_deploy_tags(force_deploy))
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


def process_policies(query):
    """Process a query that should contain policies.

    Args:
        query: Dictionary with query parameters

    Returns:
        tuple: (policy_list, packages, validated_policy)
    """
    policies_dict = parse_policies(query)
    policy_list = validate_policy_structure(policies_dict)
    mode = validate_policy_mode(policy_list[0])
    policy_instance = validate_with_custodian(policies_dict)
    tags = get_tags(mode, policy_list, query.get("force_deploy", "false").lower() == "true")
    policy_list = add_tags_to_policy(policy_list, tags)
    policy_list[0]["mode"]["role"] = query["role"]
    regions = get_policy_regions(policy_instance)
    packages = policy_list[0].get("mode", {}).get("packages", [])

    return policy_list, regions, packages


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
        policy_list, regions, packages = process_policies(query)
    except ValidationError as e:
        return_error(str(e))

    try:
        exec_options = process_exec_options(query)
    except ValidationError as e:
        return_error(f"Failed to validate execution options: {e}")

    try:
        result = process_lambda_package(query, policy_list, regions, exec_options, packages)
        return_result(result)
    except RuntimeError as e:
        return_error(f"Failed to package lambda: {e}")


if __name__ == "__main__":
    main()  # pragma: no cover
