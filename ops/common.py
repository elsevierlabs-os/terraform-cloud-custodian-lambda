#!/usr/bin/env python3
"""Common utilities for Cloud Custodian Lambda operations."""
import json
import sys
import datetime

try:
    import yaml
    from yaml import CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover
    try:
        from yaml import SafeLoader
    except ImportError:  # pragma: no cover
        SafeLoader = None

try:
    from c7n.config import Config
    from c7n.loader import PolicyLoader
    from c7n.mu import generate_requirements
    from c7n.exceptions import PolicyValidationError
    from c7n.resources.aws import get_profile_session
except ImportError:  # pragma: no cover
    print("Cloud Custodian (c7n) package is not installed. Please install it", file=sys.stderr)
    sys.exit(1)


ALLOWED_TYPES = {
    "periodic",
    "schedule",
    "config-rule",
    "config-poll-rule",
    "cloudtrail",
    "phd",
    "ec2-instance-state",
    "asg-instance-state",
    "guard-duty",
}


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def return_result(result):
    """Print result and exit."""
    print(json.dumps(result))
    sys.exit(0)


def return_error(message):
    """Print error to stderr and exit with non-zero status."""
    print(message, file=sys.stderr)
    sys.exit(1)


def format_validation_errors(errors, prefix):
    """Format validation errors consistently.

    Args:
        errors: List of error messages or error objects with message/path attributes
        prefix: Prefix for the error block

    Returns:
        Formatted error string with prefix and bulleted list
    """
    if not errors:
        return ""

    error_lines = []
    for err in errors:
        # Handle jsonschema ValidationError objects
        if hasattr(err, "message"):
            error_msg = err.message
            if hasattr(err, "path") and err.path:
                error_msg += f" (at {'.'.join(str(p) for p in err.path)})"
            error_lines.append(error_msg)
        # Handle string errors
        else:
            error_lines.append(str(err))

    # Format as bulleted list with prefix
    if prefix:
        bulleted = "\n".join(f"  - {line}" for line in error_lines)
        return f"{prefix}:\n{bulleted}"

    # No prefix: return plain errors with bullets
    return "\n".join(f"  - {line}" for line in error_lines)


def validate_format(query, key):
    """
    Validates that the relevant key in the query is JSON or YAML.

    Args:
        query: Dictionary with query parameters
        key: The key in the query dict containing the JSON/YAML string

    Returns:
       Python object based on the JSON/YAML structure (preserving order)

    Raises:
        ValidationError: If validation fails
    """
    if not query.get(key):
        raise ValidationError(f"'{key}' must be provided in query input")

    content = query[key]

    # Try JSON first
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass

    # If JSON fails, try YAML
    try:
        return yaml.load(content, Loader=SafeLoader)
    except Exception as e:
        raise ValidationError(f"Could not parse '{key}' as JSON or YAML: {e}")


def extract_named_policy(policies_dict, policy_name):
    """Extract a specific policy from multi-policy YAML while preserving vars."""
    policy_list = policies_dict.get("policies", [])

    matching_policies = [
        p for p in policy_list if isinstance(p, dict) and p.get("name") == policy_name
    ]

    if not matching_policies:
        available = [p.get("name") for p in policy_list if isinstance(p, dict)]
        raise ValidationError(f"Policy '{policy_name}' not found. Available policies: {available}")

    if len(matching_policies) > 1:
        raise ValidationError(
            f"Multiple policies with name '{policy_name}' found. Policy names must be unique."
        )

    result = {}
    if "vars" in policies_dict:
        result["vars"] = policies_dict["vars"]
    result["policies"] = matching_policies

    return result


def parse_policies(query, policies_key="policies"):
    """Parse policies and optionally extract a specific policy by name.

    Args:
        query: Dictionary with query parameters
        policies_key: Key in query containing the policies (default: "policies")

    Returns:
        Dictionary containing the parsed policies (single policy if extracted)

    Raises:
        ValidationError: If parsing or extraction fails
    """
    policy_name = query.get("policy_name", "")

    if policy_name:
        policies_dict = validate_format(query, policies_key)
        return extract_named_policy(policies_dict, policy_name)
    else:
        # Parse single policy YAML/JSON as-is
        return validate_format(query, policies_key)


def validate_policy_structure(policies_dict):
    """
    Validates that the policy contains one policy under the array policies
    and has a name.

    Args:
        policies_dict: The policies in dictionary format

    Returns:
        policy_list: List of one policy

    Raises:
        ValidationError: If validation fails
    """
    policy_list = policies_dict.get("policies", [])
    if len(policy_list) != 1:
        raise ValidationError("The 'policies' array must contain exactly one policy")

    if "name" not in policy_list[0]:
        raise ValidationError("The policy must have a name")

    return policy_list


def validate_policy_mode(policy_dict, allowed_types=ALLOWED_TYPES):
    """
    Validates that the policy dict contains mode and that this is one of the
    modes that is allowed.

    Args:
        policy_dict: A single policy in dict format
        allowed_types: The mode types that are allowed. Default is all modes
        that can be lambda

    Returns:
        mode_type

    Raises:
        ValidationError: If validation fails
    """
    mode_type = policy_dict.get("mode", {}).get("type") or "None"
    if mode_type not in allowed_types:
        raise ValidationError(
            f"Policy mode must be one of {sorted(allowed_types)} and not None "
            f"Found: {mode_type}"
        )

    return mode_type


def validate_with_custodian(policies_dict):
    """Validate using Cloud Custodian's internal validation.

    Args:
        policies_dict: Dictionary containing policy data

    Returns:
        policy_instance: The validated Cloud Custodian policy instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        loader = PolicyLoader(Config.empty())
        collection = loader.load_data(policies_dict, file_uri="-")
        for policy_instance in collection:
            policy_instance.validate()
            return policy_instance
    except PolicyValidationError as e:
        raise ValidationError(f"Policy validation error: {str(e)}")
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            f"Unexpected error during Cloud Custodian policy validation: {type(e).__name__}: {str(e)}"
        )


def get_force_deploy_tags(force_deploy):
    """Generate force deployment tags.

    Args:
        force_deploy: Boolean indicating if force deployment is enabled

    Returns:
        dict: Dictionary with force-deploy timestamp if enabled, empty dict otherwise
    """
    if not force_deploy:
        return {}

    return {"force-deploy": datetime.datetime.utcnow().isoformat() + "Z"}


def hex_ascii_encoder(digest_bytes):
    """Convert hash digest bytes to hexadecimal ASCII bytes

    Args:
        digest_bytes: Raw hash digest bytes

    Returns:
        bytes: Hexadecimal representation encoded as ASCII bytes
    """
    return digest_bytes.hex().encode("ascii")


def copy_archive(archive, hex_hash, function_name, build_root="build"):
    """Copy archive to build directory with hash-based filename

    Args:
        archive: Archive object with .path attribute
        hex_hash: Hexadecimal hash string for filename
        region: AWS region for directory structure
        function_name: Lambda function name for directory structure
        build_root: Root build directory (default: "build")

    Returns:
        str: Absolute path to the final zip file

    Raises:
        Exception: If directory creation or file copy fails
    """
    import os
    import shutil

    try:
        build_directory = os.path.join(build_root, function_name)
        if os.path.exists(build_directory):
            shutil.rmtree(build_directory)
        os.makedirs(build_directory, exist_ok=True)

        final_zip_path = os.path.join(build_directory, f"{hex_hash}.zip")
        shutil.copy2(archive.path, final_zip_path)

        return os.path.abspath(final_zip_path)
    except OSError as e:
        raise RuntimeError(f"Failed to create build directory or copy file: {e}")
    except AttributeError as e:
        raise RuntimeError(f"Archive object missing required path attribute: {e}")
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unexpected error during archive copy: {type(e).__name__}: {e}")


def get_package_versions(packages):
    """Get package versions for specified packages.

    Args:
        packages: List of package names

    Returns:
        dict: Package name to version mapping

    Raises:
        Exception: If package version generation fails
    """
    # Convert to set to remove duplicates and filter out empty/None values
    modules = {pkg.strip() for pkg in packages if pkg and pkg.strip()} if packages else set()

    # Sort for consistent output
    modules = sorted(modules)
    package_versions = {}

    try:
        requirements_content = generate_requirements(modules, include_self=True)
        for line in requirements_content.split("\n"):
            line = line.strip()
            if line and "==" in line:
                pkg, version = line.split("==", 1)
                package_versions[pkg.strip()] = version.strip()
    except ImportError as e:
        raise RuntimeError(f"Failed to import required package discovery modules: {e}")
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            f"Unexpected error during package version discovery: {type(e).__name__}: {e}"
        )

    return package_versions


def get_regions():
    """Get all enabled AWS regions using Cloud Custodian's exact approach.

    Uses the same method as Cloud Custodian's AWS provider to get enabled regions.
    This function does not fallback - it uses Cloud Custodian's method or fails.

    Returns:
        list: List of enabled AWS region names
    """

    class Options:
        profile = None

    options = Options()
    client = get_profile_session(options).client("ec2", region_name="us-east-1")

    response = client.describe_regions(
        Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}]
    )

    enabled_regions = {r["RegionName"] for r in response.get("Regions", [])}
    return list(enabled_regions)
