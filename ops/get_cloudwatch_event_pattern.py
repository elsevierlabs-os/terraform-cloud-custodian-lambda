#!/usr/bin/env python3
"""
Get CloudWatch event pattern for a Custodian policy, for use in Terraform aws_cloudwatch_event_rule.

It expects a JSON object via stdin with keys:
  - policies: (JSON or YAML)

Pattern merges with/overrides events if both provided.

Outputs:
  - event_pattern as JSON

"""

import json
import sys

from ops.common import (
    validate_policy_structure,
    return_result,
    return_error,
    validate_with_custodian,
    validate_policy_mode,
    ValidationError,
    parse_policies,
)

try:
    from c7n.mu import CloudWatchEventSource
except ImportError:  # pragma: no cover
    print(
        "Cloud Custodian (c7n) package is not installed. Please install it",
        file=sys.stderr,
    )
    sys.exit(1)


ALLOWED_TYPES = {
    "phd",
    "cloudtrail",
    "ec2-instance-state",
    "asg-instance-state",
    "guard-duty",
    "hub-finding",
}


def generate_event_pattern(event_type, events=None, pattern=None):
    """Generate CloudWatch event pattern from event type and events or pattern.

    Args:
        event_type: String event type
        events: List of events (optional)
        pattern: Dictionary with custom event pattern (optional)

    Returns:
        String representation of the event pattern

    Raises:
        ValidationError: If pattern generation fails
    """
    try:
        mode = {"type": event_type}

        # Cloud Custodian requires events to be present, so use empty list if only pattern provided
        mode["events"] = events if events is not None else []

        if pattern is not None:
            mode["pattern"] = pattern

        event_source = CloudWatchEventSource(mode, session_factory=None)
        return event_source.render_event_pattern()
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unexpected error generating event pattern: {type(e).__name__}: {e}")


def validate_event_pattern(policy_dict):
    """Validate event and or pattern exist in policy.

    Args:
        policy_dict: Dictionary of policy

    Returns:
        events: Events if found in the policy
        pattern: Pattern if found in the policy

    Raises:
        ValidationError: If neither events or pattern is found
    """
    mode = policy_dict.get("mode", {})
    if not mode.get("events") and not mode.get("pattern"):
        raise ValidationError(
            "At least one of 'mode.events' or 'mode.pattern' must be provided in the policy"
        )

    events = mode.get("events")
    pattern = mode.get("pattern")

    return events, pattern


def process_policies(query):
    """Process a query that should contain policies and return event pattern.

    Args:
        query: Dictionary with query parameters

    Returns:
        Dictionary with event_pattern as a JSON string

    Raises:
        ValidationError: If processing fails
    """
    policies_dict = parse_policies(query)
    policy_list = validate_policy_structure(policies_dict)
    event_type = validate_policy_mode(policy_list[0], ALLOWED_TYPES)
    validate_with_custodian(policies_dict)
    events, pattern = validate_event_pattern(policy_list[0])
    event_pattern = generate_event_pattern(event_type, events=events, pattern=pattern)
    return {"event_pattern": event_pattern}


def main():
    try:
        query = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        return_error(f"Failed to parse input JSON: {e}")
    except Exception as e:  # pragma: no cover
        return_error(f"Unexpected error reading input: {type(e).__name__}: {e}")

    try:
        result = process_policies(query)
        return_result(result)
    except ValidationError as e:
        return_error(str(e))
    except RuntimeError as e:
        return_error(str(e))


if __name__ == "__main__":
    main()  # pragma: no cover
