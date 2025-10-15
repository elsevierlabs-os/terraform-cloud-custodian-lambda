#!/usr/bin/env python3
"""
Validate a Cloud Custodian Lambda policy JSON.

Expects JSON input with:
- policies: dict or JSON/YAML string
- policy_name: (optional) extract specific policy from multi-policy YAML

Outputs a JSON object:
  { "valid": bool, "info_messages": [...], "error_messages": str, "policy_name": str }
"""

import json
import sys

from ops.common import (
    validate_policy_structure,
    validate_policy_mode,
    return_result,
    return_error,
    validate_with_custodian,
    ValidationError,
    parse_policies,
    format_validation_errors,
)


def create_result(valid, info_messages, error_messages, policy_name):
    """Create the result dictionary.

    Args:
        valid: Boolean indicating if validation passed
        info_messages: List of info messages
        error_messages: List of error messages
        policy_name: String policy name

    Returns:
        Dictionary with validation results
    """

    return {
        "valid": "true" if valid else "false",
        "info_messages": json.dumps(info_messages),
        "error_messages": format_validation_errors(error_messages, ""),
        "policy_name": str(policy_name),
    }


def validate_policy(policies_dict):
    """Main policy validation function.

    Args:
        policies_dict: Dictionary containing policy data

    Returns:
        Dictionary with validation results
    """
    info_messages = []
    error_messages = []
    policy_name = "N/A"

    try:
        policy_list = validate_policy_structure(policies_dict)
        policy_dict = policy_list[0]
        policy_name = policy_dict["name"]
        info_messages.append("Policy structure is correct")
    except ValidationError as e:
        error_messages.append(str(e))
        return create_result(False, info_messages, error_messages, policy_name)

    try:
        mode_type = validate_policy_mode(policy_dict)
        info_messages.append(f"Policy mode '{mode_type}' is valid")
    except ValidationError as e:
        error_messages.append(str(e))

    try:
        validate_with_custodian(policies_dict)
        info_messages.append(
            f"Cloud Custodian internal validation passed for policy '{policy_name}'"
        )
    except ValidationError as e:
        error_messages.append(str(e))

    valid = len(error_messages) == 0
    return create_result(valid, info_messages, error_messages, policy_name)


def process_policies(query):
    """Process a query that should contain policies and optionally policy_name.

    Args:
        query: Dictionary with query parameters

    Returns:
        Dictionary with validation results

    Raises:
        ValidationError: If input validation fails
    """
    policies_dict = parse_policies(query)
    return validate_policy(policies_dict)


def main():
    try:
        query = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        return_error(f"Failed to parse input JSON: {e}")
    except Exception as e:  # pragma: no cover
        return_error(f"Unexpected error reading input: {type(e).__name__}: {e}")

    try:
        result = process_policies(query)
        if result["valid"] == "false":
            # Return a more readable error message for Terraform
            error_msg = f"Policy validation failed for '{result['policy_name']}':\n{result['error_messages']}"
            return_error(error_msg)
        return_result(result)
    except ValidationError as e:
        return_error(str(e))


if __name__ == "__main__":
    main()  # pragma: no cover
