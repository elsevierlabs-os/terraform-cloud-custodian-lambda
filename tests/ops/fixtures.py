"""
Shared test fixtures for ops tests.

This module provides common test data for policies, mailer configs, and queries
to reduce repetition across test files.
"""

try:
    import yaml
    from yaml import CSafeLoader as SafeLoader
except ImportError:  # pragma: no cover
    try:
        from yaml import SafeLoader
    except ImportError:  # pragma: no cover
        SafeLoader = None


def yaml_str_to_dict(yaml_str):
    """Return a fresh valid mailer config dict (to avoid mutation issues)."""
    return yaml.load(yaml_str, Loader=SafeLoader)


SIMPLE_PERIODIC_POLICIES_YAML = """
---
policies:
  - name: test-policy
    resource: ec2
    mode:
      type: periodic
      schedule: rate(1 day)
      role: "arn:aws:iam::123456789012:role/custodian-role"
    filters:
    - and:
      - type: image-age
        days: 7
    actions:
    - stop
"""
SIMPLE_PERIODIC_POLICIES_DICT = yaml_str_to_dict(SIMPLE_PERIODIC_POLICIES_YAML)
SIMPLE_PERIODIC_POLICY_DICT = SIMPLE_PERIODIC_POLICIES_DICT["policies"][0]
SCHEDULE_POLICIES_YAML = """
---
policies:
  - name: test-policy
    resource: ec2
    mode:
      type: schedule
      schedule: rate(1 day)
      role: "arn:aws:iam::123456789012:role/custodian-role"
      group-name: my-schedule-group
    filters:
    - and:
      - type: image-age
        days: 7
    actions:
    - stop
"""
SCHEDULE_POLICIES_DICT = yaml_str_to_dict(SCHEDULE_POLICIES_YAML)
SCHEDULE_POLICY_DICT = SCHEDULE_POLICIES_DICT["policies"][0]
TOP_LEVEL_POLICY_ORDER = ["name", "resource", "mode", "filters", "actions"]
MODE_LEVEL_POLICY_ORDER = ["type", "schedule", "role"]

DUPLICATE_POLICIES_YAML = """
---
policies:
  - name: duplicate-policy-name
    resource: ec2
    mode:
      type: periodic
      schedule: rate(1 day)
      role: "arn:aws:iam::123456789012:role/custodian-role"
    filters:
    - and:
      - type: image-age
        days: 7
    actions:
    - stop
  - name: duplicate-policy-name
    resource: ec2
    mode:
      type: periodic
      schedule: rate(1 day)
      role: "arn:aws:iam::123456789012:role/custodian-role"
    filters:
    - and:
      - type: image-age
        days: 7
    actions:
    - stop
"""
DUPLICATE_POLICIES_DICT = yaml_str_to_dict(DUPLICATE_POLICIES_YAML)

MULTIPLE_POLICIES_YAML = """
---
vars:
  image-age-filters: &image-age-filters
    - type: image-age
      days: 7
policies:
  - name: ami-age
    resource: ami
    mode:
      type: periodic
      schedule: "rate(1 day)"
      role: "arn:aws:iam::123456789012:role/custodian-role"
    filters:
    - and: *image-age-filters
  - name: ec2-ami-age
    resource: ec2
    mode:
      type: periodic
      schedule: "rate(1 day)"
      role: "arn:aws:iam::123456789012:role/custodian-role"
    filters:
    - and: *image-age-filters
"""
MULTIPLE_POLICIES_DICT = yaml_str_to_dict(MULTIPLE_POLICIES_YAML)
POLICIES_ORDER = ["vars", "policies"]

INVALID_MODE_POLICIES_YAML = """---
policies:
  - name: invalid-policy
    resource: ec2
    mode:
      type: not-valid
    filters:
      - instance-state-name: running
"""
INVALID_MODE_POLICIES_DICT = yaml_str_to_dict(INVALID_MODE_POLICIES_YAML)

MISSING_MODE_POLICIES_YAML = """---
policies:
  - name: invalid-policy
    resource: ec2
    filters:
      - instance-state-name: running
"""
MISSING_MODE_POLICIES_DICT = yaml_str_to_dict(MISSING_MODE_POLICIES_YAML)

MISSING_NAME_POLICIES_YAML = """---
policies:
  - resource: ec2
    filters:
      - instance-state-name: running
"""
MISSING_NAME_POLICIES_DICT = yaml_str_to_dict(MISSING_NAME_POLICIES_YAML)

CLOUDWATCH_EVENT_POLICIES_YAML = """
---
policies:
  - name: cloudwatch-event
    resource: ec2
    mode:
      type: cloudtrail
      events:
      - source: ec2.amazonaws.com
        event: RunInstances
        ids: responseElements.instancesSet.items[].instanceId
"""
CLOUDWATCH_EVENT_POLICIES_DICT = yaml_str_to_dict(CLOUDWATCH_EVENT_POLICIES_YAML)
CLOUDWATCH_EVENT_POLICY_DICT = CLOUDWATCH_EVENT_POLICIES_DICT["policies"][0]
CLOUDWATCH_EVENT_POLICY_EVENT = CLOUDWATCH_EVENT_POLICY_DICT["mode"]["events"][0]
CLOUDWATCH_EVENT_PATTERN = {
    "detail": {"eventName": ["RunInstances"], "eventSource": ["ec2.amazonaws.com"]},
    "detail-type": ["AWS API Call via CloudTrail"],
}
INVALID_CLOUDWATCH_EVENT_POLICIES_YAML = """
---
policies:
  - name: cloudwatch-event
    resource: ec2
    mode:
      type: cloudtrail
"""
INVALID_CLOUDWATCH_EVENT_POLICIES_DICT = yaml_str_to_dict(INVALID_CLOUDWATCH_EVENT_POLICIES_YAML)
INVALID_CLOUDWATCH_EVENT_POLICY_DICT = INVALID_CLOUDWATCH_EVENT_POLICIES_DICT["policies"][0]

CONFIG_RULE_POLICIES_YAML = """
---
policies:
  - name: config-rule
    resource: ec2
    mode:
      type: config-rule
    filters:
    - instance-state-name: running
"""
CONFIG_RULE_POLICIES_DICT = yaml_str_to_dict(CONFIG_RULE_POLICIES_YAML)
CONFIG_RULE_POLICY_DICT = CONFIG_RULE_POLICIES_DICT["policies"][0]
CONFIG_RULE_EXPECTED_KEYS = {"Source", "Scope", "ConfigRuleName", "Description"}

DETAILED_POLICIES_YAML = """
---
policies:
  - name: test-policy
    resource: ec2
    mode:
      type: periodic
      schedule: rate(1 day)
      packages:
      - boto3
      - requests
      tags:
        test: "true"
      role: "arn:aws:iam::123456789012:role/custodian-role"
    conditions:
    - type: value
      key: region
      op: in
      value:
      - us-east-1
      - us-west-2
    filters:
    - and:
      - type: image-age
        days: 7
    actions:
    - stop
"""
DETAILED_POLICIES_DICT = yaml_str_to_dict(DETAILED_POLICIES_YAML)
DETAILED_POLICY_DICT = DETAILED_POLICIES_DICT["policies"][0]

EXEC_OPTIONS = {
    "region": "us-east-1",
    "log_group": "/cloud-custodian/policies",
}


def valid_mailer_config():
    """Return a fresh valid mailer config dict (to avoid mutation issues)."""
    return {
        "queue_url": "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
        "from_address": "test@example.com",
        "region": "us-east-1",
    }


def mailer_config_with_templates():
    """Return a fresh mailer config with templates (to avoid mutation issues)."""
    return {
        "queue_url": "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
        "from_address": "test@example.com",
        "region": "us-east-1",
        "templates": "test-templates-folder",
    }


def invalid_mailer_config():
    """Return a fresh invalid mailer config (to avoid mutation issues)."""
    return {
        "queueurl": "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",  # Wrong key
        "from_address": "test@example.com",
        "region": "us-east-1",
    }


def complete_mailer_config():
    """Return a complete mailer config with all defaults (as returned by validate_mailer_config).

    This includes all the fields that setup_defaults() adds, useful for testing
    functions that expect a fully-populated config.
    """
    return {
        "queue_url": "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
        "from_address": "test@example.com",
        "region": "us-east-1",
        "ses_region": "us-east-1",
        "memory": 1024,
        "runtime": "python3.11",
        "timeout": 300,
        "subnets": None,
        "security_groups": None,
        "contact_tags": [],
        "ldap_uri": None,
        "ldap_bind_dn": None,
        "ldap_bind_user": None,
        "ldap_bind_password": None,
        "endpoint_url": None,
        "datadog_api_key": None,
        "slack_token": None,
        "slack_webhook": None,
        "templates_folders": ["/path/to/templates1", "/path/to/templates2"],
    }


# Constant versions for tests that don't mutate the config
# Use the function versions (valid_mailer_config(), etc.) for tests that mutate
VALID_MAILER_CONFIG = valid_mailer_config()
MAILER_CONFIG_WITH_TEMPLATES = mailer_config_with_templates()
INVALID_MAILER_CONFIG = invalid_mailer_config()
