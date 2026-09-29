"""
Unit tests for package_lambda_policy.py.
"""

import io
import json
import os
import tempfile
import pytest

from unittest.mock import patch
from c7n.config import Config
from ops.package_lambda_policy import process_policies, ValidationError, process_exec_options

from tests.ops.fixtures import (
    SIMPLE_PERIODIC_POLICY_DICT,
    EXEC_OPTIONS,
    SIMPLE_PERIODIC_POLICIES_YAML,
    SIMPLE_PERIODIC_POLICIES_DICT,
    SCHEDULE_POLICY_DICT,
    DETAILED_POLICIES_DICT,
    DETAILED_POLICIES_YAML,
    DETAILED_POLICY_DICT,
    VARIABLE_POLICIES_DICT,
)


def fake_custodian_config(region=None, account_id=None):
    """Stand in for get_custodian_config without calling AWS."""
    return Config.empty(
        region=region or "us-east-1",
        regions=(region or "us-east-1",),
        account_id=account_id or "123456789012",
    )


def test_get_archive_success():
    """Test successful get_archive."""
    from ops.package_lambda_policy import (
        get_archive,
        create_custodian_archive,
    )

    archive = create_custodian_archive()

    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = EXEC_OPTIONS

    result = get_archive(archive, policy_list, exec_options)
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


def test_get_archive_handler_assertion_error():
    """Test get_archive with AssertionError on handler template."""
    from ops.package_lambda_policy import get_archive
    from unittest.mock import MagicMock

    # Create mock archive that raises AssertionError on first add_contents call
    mock_archive = MagicMock()
    mock_archive.add_contents.side_effect = AssertionError("Handler template error")

    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = EXEC_OPTIONS

    with pytest.raises(RuntimeError):
        get_archive(mock_archive, policy_list, exec_options)


def test_get_archive_config_assertion_error():
    """Test get_archive with AssertionError on config.json."""
    from ops.package_lambda_policy import get_archive
    from unittest.mock import MagicMock

    # Create mock archive that succeeds first call but fails second
    mock_archive = MagicMock()
    mock_archive.add_contents.side_effect = [None, AssertionError("Config error")]

    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    exec_options = EXEC_OPTIONS

    with pytest.raises(RuntimeError):
        get_archive(mock_archive, policy_list, exec_options)


def test_get_custodian_tags_schedule_mode():
    """Test get_custodian_tags with schedule mode to generate custodian-schedule tag."""
    from ops.package_lambda_policy import get_custodian_tags

    policy_list = [SCHEDULE_POLICY_DICT]
    function_name = f"custodian-{SCHEDULE_POLICY_DICT['name']}"
    query = {"function_name": function_name}

    tags = get_custodian_tags(policy_list, query)

    assert "custodian-info" in tags
    assert "mode=schedule:version=" in tags["custodian-info"]
    assert "custodian-schedule" in tags
    assert (
        tags["custodian-schedule"]
        == f"name={function_name}:group={SCHEDULE_POLICY_DICT['mode']['group-name']}"
    )


def test_process_policies_with_packages_and_tags():
    """Test parsing policy data with packages field."""
    query = {
        "policies": DETAILED_POLICIES_YAML,
        "role": "test-role",
        "execution_options": {},
    }
    with patch("ops.package_lambda_policy.get_regions", return_value=["us-east-1", "eu-west-1"]):
        with patch(
            "ops.package_lambda_policy.get_custodian_config", side_effect=fake_custodian_config
        ):
            processed_policy, condition_regions, packages = process_policies(query)

        assert condition_regions == ["us-east-1"]
        policy_list = processed_policy["us-east-1"]
        assert policy_list[0]["name"] == DETAILED_POLICY_DICT["name"]

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
        "regions": json.dumps(["us-east-1"]),
    }

    with patch("ops.package_lambda_policy.get_regions", return_value=["us-east-1", "eu-west-1"]):
        with patch(
            "ops.package_lambda_policy.get_custodian_config", side_effect=fake_custodian_config
        ):
            processed_policy, condition_regions, packages = process_policies(query)

        assert condition_regions == []
        policy_list = processed_policy["us-east-1"]
        assert policy_list[0]["name"] == SIMPLE_PERIODIC_POLICY_DICT["name"]

        # Check packages
        assert packages == []

        # Check tags
        tags = policy_list[0]["mode"]["tags"]
        assert "custodian-info" in tags
        assert "mode=periodic:version=" in tags["custodian-info"]


def test_process_policies_falls_back_to_condition_regions():
    """When no regions are requested, regions are derived from the policy's own conditions."""
    query = {
        "policies": DETAILED_POLICIES_YAML,
        "role": "test-role",
        "regions": json.dumps([]),
    }

    with patch("ops.package_lambda_policy.get_regions") as mock_get_regions:
        mock_get_regions.return_value = ["us-east-1", "us-west-2", "eu-west-1"]
        with patch(
            "ops.package_lambda_policy.get_custodian_config", side_effect=fake_custodian_config
        ):
            processed_policy, condition_regions, packages = process_policies(query)

    assert packages == DETAILED_POLICY_DICT["mode"]["packages"]
    assert set(condition_regions) == {"us-east-1", "us-west-2"}
    assert set(processed_policy) == {"us-east-1", "us-west-2"}


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
    processed_policy = {"us-east-1": [SIMPLE_PERIODIC_POLICY_DICT]}
    exec_options = {}
    regions = ["us-east-1"]
    packages = []

    result = process_lambda_package(query, processed_policy, regions, exec_options, packages)

    # Verify result structure
    assert "package_versions" in result
    assert "zips" in result

    # Verify the region map has non-empty hashes and an existing zip file
    zips = json.loads(result["zips"])
    assert len(zips["us-east-1"]["sha256_hex"]) > 0
    assert len(zips["us-east-1"]["sha256_base64"]) > 0
    assert os.path.exists(zips["us-east-1"]["path"])

    # Verify package versions
    package_versions = json.loads(result["package_versions"])
    assert "c7n" in package_versions

    # Clean up
    os.unlink(zips["us-east-1"]["path"])


def test_process_lambda_package_checksum_error():
    """Test process_lambda_package with checksum calculation failure."""
    from ops.package_lambda_policy import process_lambda_package
    from unittest.mock import Mock, patch

    query = {
        "region": "us-east-1",
        "function_name": "custodian-test-policy",
    }
    processed_policy = {"us-east-1": [SIMPLE_PERIODIC_POLICY_DICT]}
    exec_options = {}
    regions = ["us-east-1"]
    packages = []

    with patch("ops.package_lambda_policy.create_custodian_archive") as mock_create:
        mock_archive = Mock()
        mock_archive.get_checksum.side_effect = AssertionError("Mock checksum error")
        mock_create.return_value = mock_archive

        with pytest.raises(RuntimeError):
            process_lambda_package(query, processed_policy, regions, exec_options, packages)


def test_process_exec_options_not_dict():
    """Test process_exec_options when execution_options is not a dict."""
    query = {"execution_options": '"not a dict"'}

    with pytest.raises(ValidationError, match="execution_options must be a JSON object/dictionary"):
        process_exec_options(query)


def test_get_requested_regions_invalid_json():
    """Malformed 'regions' JSON raises a clear ValidationError."""
    from ops.package_lambda_policy import get_requested_regions

    with pytest.raises(ValidationError, match="Could not parse 'regions' as JSON"):
        get_requested_regions({"regions": "not-json"})


def test_get_condition_regions_with_conditions():
    """Test get_condition_regions with a policy containing region conditions."""
    from ops.package_lambda_policy import get_condition_regions
    from ops.common import validate_with_custodian

    policies_dict = DETAILED_POLICIES_DICT

    policy_instance = validate_with_custodian(policies_dict)

    with patch("ops.package_lambda_policy.get_regions") as mock_get_regions:
        mock_get_regions.return_value = ["us-east-1", "us-west-2", "eu-west-1"]

        regions = get_condition_regions(policy_instance)

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
        "condition_regions": json.dumps([]),
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


def process_variable_policies(regions):
    with patch("ops.package_lambda_policy.get_regions", return_value=regions):
        with patch(
            "ops.package_lambda_policy.get_custodian_config", side_effect=fake_custodian_config
        ):
            return process_policies(
                {
                    "policies": json.dumps(VARIABLE_POLICIES_DICT),
                    "role": "arn:aws:iam::123456789012:role/custodian-lambda",
                    "function_name": "custodian-test-variables",
                    "regions": json.dumps(regions),
                }
            )


def test_process_policies_expands_account_id_and_region():
    """Account id and region are resolved per region, with account id looked up only once."""
    regions = ["eu-west-1", "us-east-1"]

    with patch("ops.package_lambda_policy.get_regions", return_value=regions):
        with patch(
            "ops.package_lambda_policy.get_custodian_config", side_effect=fake_custodian_config
        ) as mock_config:
            processed_policy, _, _ = process_policies(
                {
                    "policies": json.dumps(VARIABLE_POLICIES_DICT),
                    "role": "arn:aws:iam::123456789012:role/custodian-lambda",
                    "function_name": "custodian-test-variables",
                    "regions": json.dumps(regions),
                }
            )

    for region in regions:
        filters = processed_policy[region][0]["filters"]
        values = {f["key"]: f["value"] for f in filters}
        assert values["tag:Account"] == "123456789012"
        assert values["tag:Region"] == region

    # get_custodian_config is called once with no account_id (to resolve it), then once per
    # region with that resolved value passed in - only the first should be missing account_id.
    resolving_calls = [c for c in mock_config.call_args_list if not c.kwargs.get("account_id")]
    assert len(resolving_calls) == 1


def test_process_policies_preserves_output_dir_for_runtime_resolution():
    """output_dir is restored after expansion, since Cloud Custodian resolves it at runtime."""
    processed_policy, _, _ = process_variable_policies(["eu-west-1"])

    policy = processed_policy["eu-west-1"][0]

    assert (
        policy["mode"]["execution-options"]["output_dir"]
        == "s3://bucket/{account_id}/{region}/logs"
    )


def test_process_lambda_package_one_archive_per_distinct_policy():
    """Regions with differing content get their own archive, matching ones share."""
    from ops.package_lambda_policy import process_lambda_package

    regions = ["eu-west-1", "us-east-1"]
    processed_policy, condition_regions, packages = process_variable_policies(regions)
    exec_options = {}

    result = process_lambda_package(
        {
            "policies": json.dumps(VARIABLE_POLICIES_DICT),
            "role": "arn:aws:iam::123456789012:role/custodian-lambda",
            "function_name": "custodian-test-variables",
            "regions": json.dumps(regions),
        },
        processed_policy,
        condition_regions,
        exec_options,
        packages,
    )
    zips = json.loads(result["zips"])

    assert set(zips) == set(regions)
    assert zips["eu-west-1"]["sha256_base64"] != zips["us-east-1"]["sha256_base64"]
    for region in regions:
        assert os.path.exists(zips[region]["path"])
        os.unlink(zips[region]["path"])


def test_process_lambda_package_shares_archive_when_content_matches():
    """Regions whose expanded policy is identical share a single archive."""
    from ops.package_lambda_policy import process_lambda_package

    regions = ["eu-west-1", "us-east-1"]
    policy_list = [SIMPLE_PERIODIC_POLICY_DICT]
    processed_policy = {region: policy_list for region in regions}
    condition_regions = []
    exec_options = {}
    packages = []

    result = process_lambda_package(
        {
            "policies": SIMPLE_PERIODIC_POLICIES_YAML,
            "role": "arn:aws:iam::123456789012:role/custodian-role",
            "function_name": "custodian-shared",
            "regions": json.dumps(regions),
        },
        processed_policy,
        condition_regions,
        exec_options,
        packages,
    )
    zips = json.loads(result["zips"])

    assert zips["eu-west-1"]["path"] == zips["us-east-1"]["path"]
    os.unlink(zips["eu-west-1"]["path"])
