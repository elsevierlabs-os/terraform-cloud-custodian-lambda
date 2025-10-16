"""
Unit tests for common.py.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch

from ops.common import (
    copy_archive,
    get_package_versions,
    validate_format,
    validate_policy_mode,
    validate_policy_structure,
    validate_with_custodian,
    ValidationError,
)
from tests.ops.fixtures import (
    SIMPLE_PERIODIC_POLICIES_DICT,
    SIMPLE_PERIODIC_POLICIES_YAML,
    TOP_LEVEL_POLICY_ORDER,
    DUPLICATE_POLICIES_DICT,
    MULTIPLE_POLICIES_YAML,
    MULTIPLE_POLICIES_DICT,
    POLICIES_ORDER,
    INVALID_MODE_POLICIES_DICT,
    MISSING_MODE_POLICIES_DICT,
    MISSING_NAME_POLICIES_DICT,
    SIMPLE_PERIODIC_POLICY_DICT,
    MODE_LEVEL_POLICY_ORDER,
)


def test_return_result(capsys):
    """Test return_result prints JSON to stdout and exits with code 0."""
    from ops.common import return_result

    test_data = {"test": "data", "number": 123}

    with pytest.raises(SystemExit) as exc_info:
        return_result(test_data)

    assert exc_info.value.code == 0

    # Check that JSON was printed to stdout
    captured = capsys.readouterr()
    assert captured.out.strip() == '{"test": "data", "number": 123}'
    assert captured.err == ""


def test_return_error(capsys):
    """Test return_error prints message to stderr and exits with code 1."""
    from ops.common import return_error

    error_message = "Test error message"

    with pytest.raises(SystemExit) as exc_info:
        return_error(error_message)

    assert exc_info.value.code == 1

    # Check that error message was printed to stderr
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() == error_message


def test_format_validation_errors_with_string_errors():
    """Test format_validation_errors with simple string error messages."""
    from ops.common import format_validation_errors

    errors = ["Error message 1", "Error message 2"]
    result = format_validation_errors(errors, "Validation failed")

    expected = "Validation failed:\n" "  - Error message 1\n" "  - Error message 2"
    assert result == expected


def test_format_validation_errors_with_jsonschema_errors():
    """Test format_validation_errors with actual jsonschema ValidationError objects."""
    import jsonschema
    from ops.common import format_validation_errors

    schema = {"type": "object", "required": ["name"], "properties": {"age": {"type": "integer"}}}
    data = {"age": "not a number"}  # Missing 'name' and wrong type for 'age'

    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    result = format_validation_errors(errors, "Schema validation failed")

    assert "Schema validation failed:" in result
    assert "'name' is a required property" in result
    assert "(at age)" in result or "age" in result.lower()


def test_validate_format_json_success():
    """Test valid JSON returned dictionary should be ordered as per original string."""

    query = {"policies": SIMPLE_PERIODIC_POLICIES_YAML}

    result = validate_format(query, "policies")

    # Check result
    assert result["policies"][0]["name"] == SIMPLE_PERIODIC_POLICY_DICT["name"]
    assert result["policies"][0]["resource"] == SIMPLE_PERIODIC_POLICY_DICT["resource"]
    assert result["policies"][0]["mode"]["type"] == SIMPLE_PERIODIC_POLICY_DICT["mode"]["type"]

    # Check top-level policy key ordering
    policy_keys = list(result["policies"][0].keys())
    assert policy_keys == TOP_LEVEL_POLICY_ORDER

    # Check nested mode key ordering
    mode_keys = list(result["policies"][0]["mode"].keys())
    assert mode_keys == MODE_LEVEL_POLICY_ORDER


def test_validate_format_yaml_success():
    """Test valid YAML returned dictionary should be ordered as per original string."""

    query = {"policies": SIMPLE_PERIODIC_POLICIES_YAML}

    result = validate_format(query, "policies")

    # Check result
    assert result["policies"][0]["name"] == SIMPLE_PERIODIC_POLICY_DICT["name"]
    assert result["policies"][0]["resource"] == SIMPLE_PERIODIC_POLICY_DICT["resource"]
    assert result["policies"][0]["mode"]["type"] == SIMPLE_PERIODIC_POLICY_DICT["mode"]["type"]

    # Check top-level policy key ordering
    policy_keys = list(result["policies"][0].keys())
    assert policy_keys == TOP_LEVEL_POLICY_ORDER

    # Check nested mode key ordering
    mode_keys = list(result["policies"][0]["mode"].keys())
    assert mode_keys == MODE_LEVEL_POLICY_ORDER


def test_validate_format_missing_key():
    """Test query with missing key."""
    query = {}

    with pytest.raises(ValidationError):
        validate_format(query, "policies")


def test_validate_format_invalid():
    """Test validation failure for invalid JSON and YAML."""
    query = {"policies": "{invalid: json: yaml}"}

    with pytest.raises(ValidationError):
        validate_format(query, "policies")


def test_extract_named_policy_not_found():
    """Test extract_named_policy when policy name is not found."""
    from ops.common import extract_named_policy

    policies_dict = SIMPLE_PERIODIC_POLICIES_DICT

    with pytest.raises(ValidationError, match="not found"):
        extract_named_policy(policies_dict, "non-existent")


def test_extract_named_policy_duplicate_names():
    """Test extract_named_policy when multiple policies have the same name."""
    from ops.common import extract_named_policy

    policies_dict = DUPLICATE_POLICIES_DICT

    with pytest.raises(ValidationError, match="Multiple policies"):
        extract_named_policy(policies_dict, "duplicate-policy-name")


def test_parse_policies_success():
    """Test successful parse_policies with named policy"""
    from ops.common import parse_policies

    policies = MULTIPLE_POLICIES_YAML
    query = {"policies": policies, "policy_name": MULTIPLE_POLICIES_DICT["policies"][0]["name"]}

    result = parse_policies(query, "policies")

    # Check that vars comes before policies in the result
    result_keys = list(result.keys())
    assert result_keys == POLICIES_ORDER

    # Check that the policy was correctly filtered
    assert result["policies"][0]["name"] == MULTIPLE_POLICIES_DICT["policies"][0]["name"]


def test_validate_policy_structure_success():
    """Test successful policy structure and ordering preservation."""
    policies_dict = SIMPLE_PERIODIC_POLICIES_DICT

    policy_list = validate_policy_structure(policies_dict)

    # Check that the structure is correct
    assert sorted(policy_list, key=lambda x: x["name"]) == sorted(
        policies_dict["policies"], key=lambda x: x["name"]
    )

    # Check that top-level policy key ordering is preserved
    policy_keys = list(policy_list[0].keys())
    assert policy_keys == TOP_LEVEL_POLICY_ORDER

    # Check nested mode key ordering
    mode_keys = list(policy_list[0]["mode"].keys())
    assert mode_keys == MODE_LEVEL_POLICY_ORDER


def test_validate_policy_structure_no_policies():
    """Test validation failure when no policies found."""
    policies_dict = {"policies": []}

    with pytest.raises(ValidationError):
        validate_policy_structure(policies_dict)


def test_validate_policy_structure_no_name():
    """Test validation failure when no policies found."""
    with pytest.raises(ValidationError):
        validate_policy_structure(MISSING_NAME_POLICIES_DICT)


def test_validate_policy_mode_success():
    """Test validation success"""
    policy_dict = SIMPLE_PERIODIC_POLICY_DICT

    mode_type = validate_policy_mode(policy_dict)
    assert mode_type == "periodic"


def test_validate_policy_mode_missing():
    """Test validation failure when mode is missing."""
    policy_dict = MISSING_MODE_POLICIES_DICT

    with pytest.raises(ValidationError):
        validate_policy_mode(policy_dict)


def test_validate_policy_mode_invalid_type():
    """Test validation failure for invalid mode type."""
    policy_dict = INVALID_MODE_POLICIES_DICT

    with pytest.raises(ValidationError):
        validate_policy_mode(policy_dict)


def test_validate_with_custodian_success():
    """Test successful Cloud Custodian validation with a correct policy."""
    policies_dict = SIMPLE_PERIODIC_POLICIES_DICT

    validate_with_custodian(policies_dict)


def test_validate_with_custodian_validation_failure():
    """Test Cloud Custodian validation failure with an invalid policy."""
    policies_dict = INVALID_MODE_POLICIES_DICT

    with pytest.raises(ValidationError):
        validate_with_custodian(policies_dict)


def test_copy_archive_oserror():
    """Test copy_archive with invalid directory permissions."""
    archive = Mock()
    archive.path = os.path.join(tempfile.gettempdir(), "test.zip")

    # Try to create in a non-existent deeply nested path that would cause OSError
    with pytest.raises(RuntimeError, match="Failed to create build directory or copy file"):
        copy_archive(archive, "testhash", "test-func", "/nonexistent/deeply/nested/path")


def test_copy_archive_missing_path():
    """Test copy_archive with archive missing path attribute."""
    archive = Mock(spec=[])  # Mock with no attributes

    with pytest.raises(RuntimeError, match="Archive object missing required path attribute"):
        copy_archive(archive, "testhash", "test-func")


def test_get_package_versions_success():
    """Test get_package_versions."""
    package_versions = get_package_versions(["c7n"])

    # Should contain c7n and its dependencies
    assert "c7n" in package_versions
    assert "boto3" in package_versions  # c7n depends on boto3
    assert "botocore" in package_versions  # boto3 depends on botocore

    # All versions should be non-empty strings
    for pkg, version in package_versions.items():
        assert version != ""
        assert version != "unknown"
        assert "." in version  # Should look like a version number


def test_get_package_versions_importerror():
    """Test get_package_versions with mocked generate_requirements ImportError failure."""

    with patch("ops.common.generate_requirements", side_effect=ImportError("Mock error")):
        with pytest.raises(
            RuntimeError, match="Failed to import required package discovery modules"
        ):
            get_package_versions(["test-package"])


def test_get_regions():

    from unittest.mock import MagicMock

    mock_client = MagicMock()
    mock_client.describe_regions.return_value = {
        "Regions": [
            {"RegionName": "us-east-1"},
            {"RegionName": "eu-west-1"},
        ]
    }
    with patch("ops.common.get_profile_session") as mock_get_profile_session:
        mock_get_profile_session.return_value.client.return_value = mock_client
        from ops.common import get_regions

        regions = get_regions()
        assert set(regions) == {"us-east-1", "eu-west-1"}


def test_get_force_deploy_tags_true():
    """Test get_force_deploy_tags when force_deploy is True."""
    from ops.package_lambda_mailer import get_force_deploy_tags

    result = get_force_deploy_tags(True)

    # Should return a dict with force-deploy key
    assert "force-deploy" in result
    assert result["force-deploy"].endswith("Z")
    # Should be an ISO 8601 timestamp
    assert "T" in result["force-deploy"]


def test_get_force_deploy_tags_false():
    """Test get_force_deploy_tags when force_deploy is False."""
    from ops.package_lambda_mailer import get_force_deploy_tags

    result = get_force_deploy_tags(False)

    # Should return an empty dict
    assert result == {}
