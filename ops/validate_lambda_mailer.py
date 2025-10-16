#!/usr/bin/env python3
"""
Validate a Cloud Custodian Lambda mailer JSON.

Expects JSON input with:
- mailer
- templates (optional)

Outputs a JSON object: { ...mailer config... }
"""

import json
import jsonschema
import sys
from os import path

try:
    import c7n_mailer
    from c7n_mailer.cli import CONFIG_SCHEMA
    from c7n_mailer.utils import setup_defaults
except ImportError:  # pragma: no cover
    print(
        "Cloud Custodian mailer (c7n-mailer) package is not installed. Please install it",
        file=sys.stderr,
    )
    sys.exit(1)

from ops.common import (
    validate_format,
    return_result,
    return_error,
    ValidationError,
    format_validation_errors,
)


def process_templates(mailer_config, templates):
    """Process template folders and add to mailer config

    Args:
        mailer_config: Dictionary with mailer configuration
        templates: Custom templates path (can be empty string)

    Returns:
        mailer_config: Config with templates_folders added
    """
    module_dir = path.dirname(path.abspath(c7n_mailer.__file__))

    default_templates = [
        path.abspath(path.join(module_dir, "msg-templates")),
        path.abspath(path.join(module_dir, "..", "msg-templates")),
        path.abspath("."),
    ]

    if templates:
        default_templates.append(path.abspath(path.expanduser(path.expandvars(templates))))

    mailer_config["templates_folders"] = default_templates

    return mailer_config


def validate_mailer_config(mailer_config):
    """Validates mailer config and adds defaults

    Args:
        mailer_dict: Dictionary

    Returns:
        mailer_config: Validated mailer config with defaults added
    """
    try:
        jsonschema.validate(mailer_config, CONFIG_SCHEMA)
    except jsonschema.exceptions.ValidationError:
        errors = list(jsonschema.Draft7Validator(CONFIG_SCHEMA).iter_errors(mailer_config))

        raise ValidationError(
            format_validation_errors(errors, "Mailer configuration validation failed")
        )

    setup_defaults(mailer_config)

    return mailer_config


def process_mailer(query):
    """Process a query that should contain mailer.

    Args:
        query: Dictionary with query parameters

    Returns:
        Dictionary with validation results

    Raises:
        ValidationError: If input validation fails
    """
    mailer_dict = validate_format(query, "mailer")
    mailer_config = validate_mailer_config(mailer_dict)

    templates = query.get("templates", "")
    mailer_config = process_templates(mailer_config, templates)

    return {"mailer_config": json.dumps(mailer_config)}


def main():
    try:
        query = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        return_error(f"Failed to parse input JSON: {e}")
    except Exception as e:  # pragma: no cover
        return_error(f"Unexpected error reading input: {type(e).__name__}: {e}")

    try:
        result = process_mailer(query)
        return_result(result)
    except ValidationError as e:
        return_error(str(e))


if __name__ == "__main__":
    main()  # pragma: no cover
