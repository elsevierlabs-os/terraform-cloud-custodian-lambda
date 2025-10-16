"""
Unit tests for get_cloudwatch_event_pattern.py script.
"""

import json
import pytest

from tests.ops.fixtures import (
    CLOUDWATCH_EVENT_POLICY_EVENT,
    CLOUDWATCH_EVENT_PATTERN,
    CLOUDWATCH_EVENT_POLICY_DICT,
    CLOUDWATCH_EVENT_POLICIES_YAML,
    INVALID_CLOUDWATCH_EVENT_POLICY_DICT,
)


def test_generate_event_pattern_success():
    """Test successful event pattern generation with Cloud Custodian."""
    from ops.get_cloudwatch_event_pattern import generate_event_pattern

    events = [CLOUDWATCH_EVENT_POLICY_EVENT]

    result = generate_event_pattern("cloudtrail", events, None)

    parsed_result = json.loads(result)

    assert parsed_result == CLOUDWATCH_EVENT_PATTERN


def test_generate_event_pattern_failure():
    """Test event pattern generation failure."""
    from ops.get_cloudwatch_event_pattern import generate_event_pattern, ValidationError

    with pytest.raises(ValidationError):
        generate_event_pattern("invalid-type", ["ReadOnly"], {})


def test_generate_event_pattern_with_pattern():
    """Test event pattern generation with custom pattern."""
    from ops.get_cloudwatch_event_pattern import generate_event_pattern

    result = generate_event_pattern("cloudtrail", None, CLOUDWATCH_EVENT_PATTERN)

    assert json.loads(result) == CLOUDWATCH_EVENT_PATTERN


def test_validate_event_pattern_success():
    """Test successful validate event pattern with events"""
    from ops.get_cloudwatch_event_pattern import validate_event_pattern

    policy_dict = CLOUDWATCH_EVENT_POLICY_DICT

    events, pattern = validate_event_pattern(policy_dict)
    assert events == [CLOUDWATCH_EVENT_POLICY_EVENT]
    assert pattern is None


def test_validate_event_pattern_failure():
    """Test failure validate event pattern where neither events or pattern are supplied"""
    from ops.get_cloudwatch_event_pattern import validate_event_pattern, ValidationError

    policy_dict = INVALID_CLOUDWATCH_EVENT_POLICY_DICT

    with pytest.raises(ValidationError):
        validate_event_pattern(policy_dict)


def test_process_policies_success():
    """Test successful end-to-end process."""
    from ops.get_cloudwatch_event_pattern import process_policies

    query = {"policies": CLOUDWATCH_EVENT_POLICIES_YAML}

    result = process_policies(query)["event_pattern"]

    parsed_result = json.loads(result)

    assert parsed_result == CLOUDWATCH_EVENT_PATTERN


def test_main_success():
    """Test main function with valid input."""
    import io
    from unittest.mock import patch
    from ops.get_cloudwatch_event_pattern import main

    valid_input = {"policies": CLOUDWATCH_EVENT_POLICIES_YAML}

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_main_json_decode_error(capsys):
    """Test main function with invalid JSON input."""
    import io
    from unittest.mock import patch
    from ops.get_cloudwatch_event_pattern import main

    with patch("sys.stdin", io.StringIO("invalid json")):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0


def test_main_validation_error(capsys):
    """Test main function with validation error."""
    import io
    from unittest.mock import patch
    from ops.get_cloudwatch_event_pattern import main

    invalid_input = {"policies": "{}"}

    with patch("sys.stdin", io.StringIO(json.dumps(invalid_input))):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert len(captured.err) > 0


def test_main_runtime_error(capsys):
    """Test main function with RuntimeError from process_policies."""
    import io
    from unittest.mock import patch
    from ops.get_cloudwatch_event_pattern import main

    valid_input = {"policies": "{}"}

    with patch("sys.stdin", io.StringIO(json.dumps(valid_input))):
        with patch(
            "ops.get_cloudwatch_event_pattern.process_policies",
            side_effect=RuntimeError("Processing failed"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert len(captured.err) > 0
