"""
Unit tests for validate_lambda_mailer.py script.
"""

import io
import json
import pytest

from unittest.mock import patch
from ops.validate_lambda_mailer import main, process_mailer, validate_mailer_config, ValidationError
from tests.ops.fixtures import (
    valid_mailer_config,
    VALID_MAILER_CONFIG,
    INVALID_MAILER_CONFIG,
    MAILER_CONFIG_WITH_TEMPLATES,
)


def test_validate_mailer_config_success():
    """Test successful mailer config validation."""
    config = VALID_MAILER_CONFIG
    result = validate_mailer_config(config)

    # Check that defaults were added
    assert "memory" in result
    assert "timeout" in result
    assert "runtime" in result

    # Check that original required fields are preserved
    assert result["queue_url"] == VALID_MAILER_CONFIG["queue_url"]
    assert result["from_address"] == VALID_MAILER_CONFIG["from_address"]
    assert result["region"] == VALID_MAILER_CONFIG["region"]


def test_validate_mailer_config_failure():
    """Test mailer config validation with incorrect schema."""
    with pytest.raises(ValidationError):
        validate_mailer_config(INVALID_MAILER_CONFIG)


def test_process_templates():
    """Test process templates."""
    from ops.validate_lambda_mailer import process_templates

    templates = MAILER_CONFIG_WITH_TEMPLATES["templates"]

    result = process_templates(MAILER_CONFIG_WITH_TEMPLATES, templates)

    templates_folders = result["templates_folders"]
    assert len(templates_folders) == 4
    matching = [
        folder
        for folder in templates_folders
        if MAILER_CONFIG_WITH_TEMPLATES["templates"] in folder
    ]
    assert len(matching) == 1


def test_process_mailer_success():
    """Test successful mailer processing"""
    config = valid_mailer_config()
    query = {"mailer": json.dumps(config)}

    result = process_mailer(query)

    mailer_config = json.loads(result["mailer_config"])
    assert mailer_config["queue_url"] == config["queue_url"]
    assert mailer_config["memory"] == 1024

    templates_folders = mailer_config["templates_folders"]
    assert len(templates_folders) == 3


def test_process_mailer_failure():
    """Test mailer processing with missing key"""
    query = {}

    with pytest.raises(ValidationError):
        process_mailer(query)


def test_main_success():
    """Test main function with valid input."""
    valid_input = {"mailer": json.dumps(valid_mailer_config())}

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
    invalid_input = {"mailer": "{}"}

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0
