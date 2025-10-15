#!/usr/bin/env python3
"""
Get the config rule parameters for a config-rule or config-poll-rule Custodian policy, for use in Terraform aws_config_config_rule.

This script is designed for use as a Terraform external data source using query.
It expects a JSON object via stdin with keys:
  - policies: (JSON or YAML)

Outputs a JSON object: { ...config rule params... }
"""

import json
import sys

from types import SimpleNamespace
from ops.common import (
    validate_format,
    validate_policy_structure,
    validate_policy_mode,
    validate_with_custodian,
    ValidationError,
    return_result,
    return_error,
)

try:
    from c7n.mu import ConfigRule, PolicyLambda
    from c7n.policy import Policy
    from c7n.resources import load_resources
    from c7n.schema import StructureParser
    from c7n.exceptions import PolicyValidationError
except ImportError:  # pragma: no cover
    print(
        "Cloud Custodian (c7n) package is not installed. Please install it",
        file=sys.stderr,
    )
    sys.exit(1)


ALLOWED_TYPES = ("config-rule", "config-poll-rule")


def create_policy_objects(policy_dict):
    """Create policy_lambda and config_rule from policy.

    Args:
        policy_dict: Dictionary containing policy configuration

    Returns:
        Tuple of (policy_lambda, config_rule)

    Raises:
        ValidationError: If object creation fails
    """
    try:
        policy_structure = {"policies": [policy_dict]}
        structure = StructureParser()
        structure.validate(policy_structure)
        rtypes = structure.get_resource_types(policy_structure)
        load_resources(rtypes)

        options = SimpleNamespace(
            region="us-east-1",
            profile=None,
            assume_role=None,
            session_policy=None,
            external_id=None,
            account_id=None,
            role=None,
            session_name=None,
            metrics=None,
            metrics_enabled=False,
            tracer=None,
            cache=None,
            cache_period=0,
        )

        policy = Policy(policy_dict, options=options)
        policy_lambda = PolicyLambda(policy)
        policy_lambda.arn = "arn:aws:lambda:us-east-1:123456789012:function:dummy"
        config_rule = ConfigRule(policy_dict["mode"], session_factory=None)

        return policy_lambda, config_rule
    except PolicyValidationError as e:
        raise ValidationError(str(e))
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unexpected error creating policy objects: {type(e).__name__}: {e}")


def extract_config_rule_params(policy_lambda, config_rule):
    """Extract config rule parameters.

    Args:
        policy_lambda: PolicyLambda instance
        config_rule: ConfigRule instance

    Returns:
        Dictionary with config rule parameters

    Raises:
        ValidationError: If parameter extraction fails
    """
    try:
        params = config_rule.get_rule_params(policy_lambda)
        # Convert non-string values to JSON strings for Terraform compatibility
        result = {k: (json.dumps(v) if not isinstance(v, str) else v) for k, v in params.items()}
        return result
    except AttributeError as e:
        raise RuntimeError(f"Failed to extract config rule parameters: {type(e).__name__}: {e}")
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            f"Unexpected error during extraction of config rule parameters: {type(e).__name__}: {e}"
        )


def process_policies(query):
    """Process a query that should contain policies and return config rule parameters.

    Args:
        query: Dictionary with query parameters

    Returns:
        Dictionary with config rule parameters

    Raises:
        ValidationError: If processing fails
    """
    policies_dict = validate_format(query, "policies")
    policy_list = validate_policy_structure(policies_dict)
    validate_policy_mode(policy_list[0], ALLOWED_TYPES)
    validate_with_custodian(policies_dict)
    policy_lambda, config_rule = create_policy_objects(policy_list[0])
    return extract_config_rule_params(policy_lambda, config_rule)


def main():
    try:
        query = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        return_error(f"Failed to parse input JSON: {e}")
    except Exception as e:  # pragma: no cover
        return_error(f"Unexpected error reading input: {type(e).__name__}: {e}")

    try:
        params = process_policies(query)
        return_result(params)
    except ValidationError as e:
        return_error(str(e))
    except RuntimeError as e:
        return_error(str(e))


if __name__ == "__main__":
    main()  # pragma: no cover
