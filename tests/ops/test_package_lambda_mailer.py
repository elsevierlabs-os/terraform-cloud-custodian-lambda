"""
Unit tests for package_lambda_mailer.py.
"""

import json
import tempfile
import os
import io
import pytest
from unittest.mock import patch
from c7n_mailer import deploy as c7n_mailer_deploy

from ops.package_lambda_mailer import process_lambda_package, main
from tests.ops.fixtures import (
    complete_mailer_config,
)


def test_process_lambda_package_success():
    """Test successful process_lambda_package."""
    query = {
        "region": "us-east-1",
        "lambda_name": "cloud-custodian-mailer",
        "mailer_config": json.dumps(complete_mailer_config()),
    }

    result = process_lambda_package(query)

    # Verify result structure
    assert "sha256_hex" in result
    assert "sha256_base64" in result
    assert "zip_path" in result
    assert "package_versions" in result

    # Verify hashes are non-empty
    assert len(result["sha256_hex"]) > 0
    assert len(result["sha256_base64"]) > 0

    # Verify zip file exists
    assert os.path.exists(result["zip_path"])

    # Verify package versions
    package_versions = json.loads(result["package_versions"])
    assert "c7n-mailer" in package_versions

    # Clean up
    os.unlink(result["zip_path"])


def test_process_lambda_package_oserror():
    """Test process_lambda_package handles OSError during archive creation."""
    query = {
        "region": "us-east-1",
        "lambda_name": "cloud-custodian-mailer",
        "mailer_config": json.dumps(complete_mailer_config()),
    }

    with patch.object(c7n_mailer_deploy, "get_archive") as mock_get_archive:
        mock_get_archive.side_effect = OSError("Permission denied")

        with pytest.raises(RuntimeError):
            process_lambda_package(query)


def test_process_lambda_package_assertion_error():
    """Test process_lambda_package handles AssertionError during checksum calculation."""
    from unittest.mock import MagicMock

    query = {
        "region": "us-east-1",
        "lambda_name": "cloud-custodian-mailer",
        "mailer_config": json.dumps(complete_mailer_config()),
    }

    mock_archive = MagicMock()
    mock_archive.get_checksum.side_effect = AssertionError("Invalid archive state")

    with patch.object(c7n_mailer_deploy, "get_archive", return_value=mock_archive):
        with pytest.raises(RuntimeError):
            process_lambda_package(query)


def test_main_success():
    """Test main function with successful execution."""
    valid_input = {
        "region": "us-east-1",
        "lambda_name": "cloud-custodian-mailer",
        "mailer_config": json.dumps(complete_mailer_config()),
    }

    mock_result = {
        "sha256_hex": "abcd1234",
        "sha256_base64": "base64hash",
        "zip_path": os.path.join(tempfile.gettempdir(), "test.zip"),
        "package_versions": json.dumps({"c7n-mailer": "1.0.0"}),
    }

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with patch("ops.package_lambda_mailer.process_lambda_package", return_value=mock_result):
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


def test_main_missing_required_fields(capsys):
    """Test main function with missing required fields."""
    incomplete_input = {
        "mailer_config": json.dumps(complete_mailer_config()),
    }

    with patch("sys.stdin", io.StringIO(json.dumps(incomplete_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0


def test_main_runtime_error(capsys):
    """Test main function handling RuntimeError from process_lambda_package."""
    valid_input = {
        "region": "us-east-1",
        "lambda_name": "cloud-custodian-mailer",
        "mailer_config": json.dumps(complete_mailer_config()),
    }

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with patch("ops.package_lambda_mailer.process_lambda_package") as mock_process:
            mock_process.side_effect = RuntimeError("Archive creation failed")
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert len(captured.err) > 0
