"""
Unit tests for package_lambda_policy.py.
"""

import io
import json
import os
import tempfile
import pytest

from unittest.mock import patch
from ops.package_lambda_policy import process_policies, ValidationError, process_exec_options

from tests.ops.fixtures import (
    SIMPLE_PERIODIC_POLICY_DICT,
    EXEC_OPTIONS,
    SIMPLE_PERIODIC_POLICIES_YAML,
    SIMPLE_PERIODIC_POLICIES_DICT,
    DETAILED_POLICIES_DICT,
    DETAILED_POLICIES_YAML,
    DETAILED_POLICY_DICT,
)


def test_add_handler_and_config_to_archive_success():
    """Test successful add_handler_and_config_to_archive."""
    from ops.package_lambda_policy import (
        add_handler_and_config_to_archive,
        create_custodian_archive,
    )

    archive = create_custodian_archive()

    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = EXEC_OPTIONS

    result = add_handler_and_config_to_archive(archive, policy_list, exec_options)
    assert result == archive

    archive.close()
    filenames = archive.get_filenames()

    assert "custodian_policy.py" in filenames, "Archive should contain handler file"
    assert "config.json" in filenames, "Archive should contain config file"

    with archive.get_reader() as reader:
        config_content = reader.read("config.json").decode("utf-8")
        config_data = json.loads(config_content)
        assert "execution-options" in config_data
        assert "policies" in config_data
        assert config_data["execution-options"] == exec_options
        assert config_data["policies"] == policy_list

    archive.remove()


def test_add_handler_and_config_to_archive_handler_assertion_error():
    """Test add_handler_and_config_to_archive with AssertionError on handler template."""
    from ops.package_lambda_policy import add_handler_and_config_to_archive
    from unittest.mock import MagicMock

    # Create mock archive that raises AssertionError on first add_contents call
    mock_archive = MagicMock()
    mock_archive.add_contents.side_effect = AssertionError("Handler template error")

    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = EXEC_OPTIONS

    with pytest.raises(RuntimeError):
        add_handler_and_config_to_archive(mock_archive, policy_list, exec_options)


def test_add_handler_and_config_to_archive_config_assertion_error():
    """Test add_handler_and_config_to_archive with AssertionError on config.json."""
    from ops.package_lambda_policy import add_handler_and_config_to_archive
    from unittest.mock import MagicMock

    # Create mock archive that succeeds first call but fails second
    mock_archive = MagicMock()
    mock_archive.add_contents.side_effect = [None, AssertionError("Config error")]

    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = EXEC_OPTIONS

    with pytest.raises(RuntimeError):
        add_handler_and_config_to_archive(mock_archive, policy_list, exec_options)


def test_process_policies_with_packages_and_tags():
    """Test parsing policy data with packages field."""
    query = {"policies": DETAILED_POLICIES_YAML, "role": "test-role", "execution_options": {}}
    with patch("ops.package_lambda_policy.get_regions", return_value=["us-east-1", "eu-west-1"]):
        policy_list, regions, packages = process_policies(query)
        assert policy_list[0]["name"] == SIMPLE_PERIODIC_POLICY_DICT["name"]

        # Check packages
        assert packages == DETAILED_POLICY_DICT["mode"]["packages"]

        # Check tags
        tags = policy_list[0]["mode"]["tags"]
        assert "test" in tags
        assert tags["test"] == "true"
        assert "custodian-info" in tags
        assert "mode=periodic:version=" in tags["custodian-info"]


def test_process_policies_without_packages_and_tags():
    """Test parsing policy data without packages field."""
    query = {
        "policies": SIMPLE_PERIODIC_POLICIES_YAML,
        "role": "test-role",
    }

    with patch("ops.package_lambda_policy.get_regions", return_value=["us-east-1", "eu-west-1"]):

        policy_list, regions, packages = process_policies(query)
        assert policy_list[0]["name"] == SIMPLE_PERIODIC_POLICY_DICT["name"]

        # Check packages
        assert packages == []

        # Check tags
        tags = policy_list[0]["mode"]["tags"]
        assert "custodian-info" in tags
        assert "mode=periodic:version=" in tags["custodian-info"]


def test_process_exec_options_success():
    """Test parsing correct execution_options"""

    query = {
        "policies": SIMPLE_PERIODIC_POLICIES_YAML,
        "execution_options": json.dumps(EXEC_OPTIONS),
    }
    exec_options = process_exec_options(query)

    assert exec_options == {"log_group": EXEC_OPTIONS["log_group"]}


def test_process_exec_options_failure():
    """Test parsing incorrect execution_options"""

    query = {
        "policies": SIMPLE_PERIODIC_POLICIES_YAML,
        "execution_options": "not-valid",
    }
    with pytest.raises(ValidationError):
        process_exec_options(query)


def test_process_exec_options_empty():
    """Test parsing empty execution_options"""

    query = {
        "policies": SIMPLE_PERIODIC_POLICIES_YAML,
        "execution_options": json.dumps({}),
    }
    exec_options = process_exec_options(query)

    assert exec_options == {}


def test_create_custodian_archive():
    """Test create_custodian_archive function."""
    from ops.package_lambda_policy import create_custodian_archive

    archive = create_custodian_archive()
    assert archive is not None

    archive.close()

    filenames = archive.get_filenames()
    c7n_files = [f for f in filenames if f.startswith("c7n/")]
    assert len(c7n_files) > 0, "Archive should contain c7n module files"

    archive.remove()


def test_create_custodian_archive_with_packages():
    """Test create_custodian_archive with additional packages."""
    from ops.package_lambda_policy import create_custodian_archive

    # Test with additional packages that should be available
    packages = ["json"]
    archive = create_custodian_archive(packages=packages)
    assert archive is not None

    archive.close()

    # Verify it has c7n module and json
    filenames = archive.get_filenames()
    c7n_files = [f for f in filenames if f.startswith("c7n/")]
    json_files = [f for f in filenames if f.startswith("json/")]
    assert len(c7n_files) > 0, "Archive should contain c7n module files"
    assert len(json_files) > 0, "Archive should contain json module files"

    archive.remove()


def test_end_to_end_archive_creation():
    """Test the full archive creation process."""
    from ops.package_lambda_policy import process_lambda_package

    query = {
        "region": "us-east-1",
        "function_name": "custoian-test-policy",
    }
    policies = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = {}
    regions = ["us-east-1"]
    packages = []

    result = process_lambda_package(query, policies, regions, exec_options, packages)

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
    assert "c7n" in package_versions

    # Clean up
    os.unlink(result["zip_path"])


def test_process_lambda_package_checksum_error():
    """Test process_lambda_package with checksum calculation failure."""
    from ops.package_lambda_policy import process_lambda_package
    from unittest.mock import Mock, patch

    query = {
        "region": "us-east-1",
        "function_name": "custodian-test-policy",
    }
    policies = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = {}
    regions = ["us-east-1"]
    packages = []

    with patch("ops.package_lambda_policy.create_custodian_archive") as mock_create:
        mock_archive = Mock()
        mock_archive.get_checksum.side_effect = AssertionError("Mock checksum error")
        mock_create.return_value = mock_archive

        with pytest.raises(RuntimeError):
            process_lambda_package(query, policies, regions, exec_options, packages)


def test_process_exec_options_not_dict():
    """Test process_exec_options when execution_options is not a dict."""
    query = {"execution_options": '"not a dict"'}

    with pytest.raises(ValidationError, match="execution_options must be a JSON object/dictionary"):
        process_exec_options(query)


def test_get_policy_regions_with_conditions():
    """Test get_policy_regions with a policy containing region conditions."""
    from ops.package_lambda_policy import get_policy_regions
    from ops.common import validate_with_custodian

    policies_dict = DETAILED_POLICIES_DICT

    policy_instance = validate_with_custodian(policies_dict)

    with patch("ops.package_lambda_policy.get_regions") as mock_get_regions:
        mock_get_regions.return_value = ["us-east-1", "us-west-2", "eu-west-1"]

        regions = get_policy_regions(policy_instance)

        assert "us-east-1" in regions
        assert "us-west-2" in regions
        assert "eu-west-1" not in regions


def test_policy_contains_conditions_false():
    """Test policy_contains_conditions when conditions is None."""
    from ops.package_lambda_policy import policy_contains_conditions
    from ops.common import validate_with_custodian

    policies_dict = SIMPLE_PERIODIC_POLICIES_DICT

    policy_instance = validate_with_custodian(policies_dict)

    result = policy_contains_conditions(policy_instance)
    assert not result


def test_policy_contains_conditions_true():
    """Test policy_contains_conditions when conditions exist."""
    from ops.package_lambda_policy import policy_contains_conditions
    from ops.common import validate_with_custodian

    policies_dict = DETAILED_POLICIES_DICT

    policy_instance = validate_with_custodian(policies_dict)

    result = policy_contains_conditions(policy_instance)
    assert result


def test_main_success():
    """Test main function with valid input."""
    from ops.package_lambda_policy import main

    valid_input = {
        "policies": DETAILED_POLICIES_YAML,
        "execution_options": EXEC_OPTIONS,
        "function_name": "test-function",
        "role": "arn:aws:iam::123456789012:role/test-role",
    }

    mock_policy = {
        "name": "test-policy",
        "resource": "ec2",
        "mode": {
            "type": "periodic",
        },
    }

    mock_result = {
        "sha256_hex": "abcd1234",
        "sha256_base64": "base64hash",
        "zip_path": os.path.join(tempfile.gettempdir(), "test.zip"),
        "package_versions": json.dumps({"c7n": "1.0.0"}),
        "custodian_tags": json.dumps({"custodian-info": "mode=periodic:version=0.9.0"}),
        "policy_regions": json.dumps([]),
    }

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with patch("ops.package_lambda_policy.process_lambda_package", return_value=mock_result):
            with patch(
                "ops.package_lambda_policy.process_policies",
                return_value=([mock_policy], set([]), []),
            ):
                with patch(
                    "ops.package_lambda_policy.process_exec_options",
                    return_value={"log_group": EXEC_OPTIONS["log_group"]},
                ):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 0


def test_main_json_decode_error(capsys):
    """Test main function with invalid JSON input."""
    from ops.package_lambda_policy import main

    with patch("sys.stdin", io.StringIO("invalid json")):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Failed to parse input JSON" in captured.err


def test_main_missing_required_fields(capsys):
    """Test main function with missing required fields."""
    from ops.package_lambda_policy import main

    invalid_input = {"policies": json.dumps({"policies": [{"name": "test"}]})}

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing required fields" in captured.err


def test_main_validation_error(capsys):
    """Test main function with policy validation error from process_policies."""
    from ops.package_lambda_policy import main, ValidationError

    invalid_input = {
        "policies": json.dumps({"policies": []}),
        "execution_options": json.dumps({}),
        "function_name": "test-function",
        "role": "arn:aws:iam::123456789012:role/test-role",
    }

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with patch(
            "ops.package_lambda_policy.process_policies",
            side_effect=ValidationError("Policy validation failed"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Policy validation failed" in captured.err


def test_main_exec_options_validation_error(capsys):
    """Test main function with execution options validation error."""
    from ops.package_lambda_policy import main

    invalid_input = {
        "policies": SIMPLE_PERIODIC_POLICIES_YAML,
        "execution_options": "not valid json",
        "function_name": "test-function",
        "role": "arn:aws:iam::123456789012:role/test-role",
    }

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with patch(
            "ops.package_lambda_policy.process_policies",
            return_value=([{"name": "test"}], [], []),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Failed to validate execution options" in captured.err


def test_main_runtime_error(capsys):
    """Test main function with runtime error during packaging."""
    from ops.package_lambda_policy import main

    valid_input = {
        "policies": SIMPLE_PERIODIC_POLICIES_YAML,
        "execution_options": json.dumps(EXEC_OPTIONS),
        "function_name": "test-function",
        "role": "arn:aws:iam::123456789012:role/test-role",
    }

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with patch(
            "ops.package_lambda_policy.process_policies",
            return_value=([{"name": "test"}], ["us-east-1"], []),
        ):
            with patch(
                "ops.package_lambda_policy.process_exec_options", return_value={"log_group": "test"}
            ):
                with patch("ops.package_lambda_policy.process_lambda_package") as mock_package:
                    mock_package.side_effect = RuntimeError("Mock packaging error")

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1
                    captured = capsys.readouterr()
                    assert "Failed to package lambda" in captured.err
