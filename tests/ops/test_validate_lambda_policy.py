"""
Unit tests for validate_lambda_policy.py script.
"""

import io
import json
import pytest

from unittest.mock import patch
from ops.validate_lambda_policy import main, process_policies, validate_policy
from tests.ops.fixtures import (
    SIMPLE_PERIODIC_POLICIES_YAML,
    INVALID_MODE_POLICIES_YAML,
)


def test_validate_policy_incorrect_structure():
    """Test validate_policy with incorrect structure"""

    policies_dict = {"policies": []}
    result = validate_policy(policies_dict)

    assert result["valid"] == "false"
    assert result["policy_name"] == "N/A"
    assert "error_messages" in result


def test_process_policies_success():
    """Test successful query processing."""

    query = {"policies": SIMPLE_PERIODIC_POLICIES_YAML}

    result = process_policies(query)

    assert result["valid"] == "true"
    assert result["policy_name"] == "test-policy"


def test_process_policies_failure():
    """Test query processing fails with an invalid policy."""

    query = {"policies": INVALID_MODE_POLICIES_YAML}

    result = process_policies(query)

    assert result["valid"] == "false"
    # policy mode type and cloud custodian validation should both fail
    # Check that error_messages contains both error messages
    assert "Policy mode must be" in result["error_messages"]
    assert "Policy validation error" in result["error_messages"]


def test_main_success():
    """Test main function with valid input."""
    valid_input = {"policies": SIMPLE_PERIODIC_POLICIES_YAML}

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
    invalid_input = {"policies": INVALID_MODE_POLICIES_YAML}

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0


def test_main_missing_policies_key(capsys):
    """Test main function when policies key is missing from query."""
    invalid_input = {"not_policies": "some value"}

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "policies" in captured.err.lower()
