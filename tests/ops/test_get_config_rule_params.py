"""
Unit tests for get_config_rule_params.py script.
"""

import json
import pytest
import io
from unittest.mock import patch

from ops.get_config_rule_params import (
    create_policy_objects,
    extract_config_rule_params,
    main,
    ValidationError,
)

from tests.ops.fixtures import (
    CONFIG_RULE_POLICIES_YAML,
    CONFIG_RULE_POLICY_DICT,
    CONFIG_RULE_EXPECTED_KEYS,
)


def test_create_policy_objects_success():
    """Test successful policy object creation with Cloud Custodian."""
    policy_data = CONFIG_RULE_POLICY_DICT

    policy_lambda, config_rule = create_policy_objects(policy_data)

    assert policy_lambda is not None
    assert config_rule is not None


def test_create_policy_objects_failure():
    """Test policy object creation failure with invalid policy data."""
    # Missing required fields (resource and mode) should cause failure
    invalid_policy_data = {
        "name": "test-policy",
    }

    with pytest.raises(ValidationError):
        create_policy_objects(invalid_policy_data)


def test_extract_config_rule_params_success():
    """Test successful config rule parameter extraction."""
    policy_data = CONFIG_RULE_POLICY_DICT

    policy_lambda, config_rule = create_policy_objects(policy_data)

    result = extract_config_rule_params(policy_lambda, config_rule)
    assert isinstance(result, dict)

    # Should contain the standard AWS Config rule parameters
    assert set(result.keys()) == CONFIG_RULE_EXPECTED_KEYS

    # All values should be strings (JSON-serialized for Terraform compatibility)
    for key, value in result.items():
        assert isinstance(key, str)
        assert isinstance(value, str)

    # Validate the Source parameter
    source = json.loads(result["Source"])
    assert source["Owner"] == "CUSTOM_LAMBDA"
    assert source["SourceIdentifier"] == "arn:aws:lambda:us-east-1:123456789012:function:dummy"
    assert "SourceDetails" in source
    assert source["SourceDetails"][0]["EventSource"] == "aws.config"
    assert source["SourceDetails"][0]["MessageType"] == "ConfigurationItemChangeNotification"

    # Validate the Scope parameter
    scope = json.loads(result["Scope"])
    assert "ComplianceResourceTypes" in scope
    assert "AWS::EC2::Instance" in scope["ComplianceResourceTypes"]

    # Validate other parameters
    assert result["ConfigRuleName"] == "custodian-config-rule"
    assert result["Description"] == "cloud-custodian lambda policy"


def test_extract_config_rule_params_failure():
    """Test config rule parameter extraction failure."""
    # Create valid objects first
    valid_policy_data = CONFIG_RULE_POLICY_DICT

    policy_lambda, config_rule = create_policy_objects(valid_policy_data)

    # Empty the config_rule object to cause get_rule_params to fail
    config_rule.data = None

    with pytest.raises(RuntimeError):
        extract_config_rule_params(policy_lambda, config_rule)


def test_process_policies_success():
    """Test successful end-to-end process."""
    from ops.get_config_rule_params import process_policies

    query = {"policies": CONFIG_RULE_POLICIES_YAML}

    result = process_policies(query)

    # Validate the Source parameter
    source = json.loads(result["Source"])
    assert source["Owner"] == "CUSTOM_LAMBDA"
    assert source["SourceIdentifier"] == "arn:aws:lambda:us-east-1:123456789012:function:dummy"
    assert "SourceDetails" in source
    assert source["SourceDetails"][0]["EventSource"] == "aws.config"
    assert source["SourceDetails"][0]["MessageType"] == "ConfigurationItemChangeNotification"

    # Validate the Scope parameter
    scope = json.loads(result["Scope"])
    assert "ComplianceResourceTypes" in scope
    assert "AWS::EC2::Instance" in scope["ComplianceResourceTypes"]

    # Validate other parameters
    assert result["ConfigRuleName"] == "custodian-config-rule"
    assert result["Description"] == "cloud-custodian lambda policy"


def test_main_success():
    """Test main function with valid input."""
    valid_input = {"policies": CONFIG_RULE_POLICIES_YAML}

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_main_json_decode_error(capsys):
    """Test main function with invalid JSON input."""
    with patch("sys.stdin", io.StringIO("invalid json")):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0


def test_main_validation_error(capsys):
    """Test main function with validation error."""
    invalid_input = {"policies": "{}"}

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0


def test_main_runtime_error(capsys):
    """Test main function with RuntimeError from process_policies."""
    valid_input = {"policies": "{}"}

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with patch(
            "ops.get_config_rule_params.process_policies",
            side_effect=RuntimeError("Processing failed"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert len(captured.err) > 0
