#!/usr/bin/env python3
"""
Package a Lambda function for Cloud Custodian

This script leverages Cloud Custodian code to dynamically create lambda archives
for custodian mailer.
Config.json is generated from inputs.

Expects JSON input with:
- mailer_config

Outputs information regarding the zip created in JSON format:
- sha256_hex
- sha256_base64
- zip_path
- package_versions
"""

import hashlib
import json
import sys

from ops.common import (
    validate_format,
    return_result,
    return_error,
    hex_ascii_encoder,
    copy_archive,
    get_package_versions,
    get_force_deploy_tags,
)

try:
    from c7n_mailer.deploy import get_archive
except ImportError:  # pragma: no cover
    print(
        "Cloud Custodian (c7n) or c7n_mailer package is not installed. Please install it",
        file=sys.stderr,
    )
    sys.exit(1)


# WORKAROUND: Not using upstream as need to add jwt
# Issue: https://github.com/cloud-custodian/cloud-custodian/issues/10282
# Once fixed can change back to import it/from c7n_mailer.deploy import CORE_DEPS
CORE_DEPS = [
    # core deps
    "jinja2",
    "markupsafe",
    "yaml",
    "ldap3",
    "pyasn1",
    "redis",
    "jmespath",
    "jwt",
    # for other dependencies
    "pkg_resources",
    # transport datadog - recursive deps
    "datadog",
    "decorator",
    # requests (recursive deps), needed by datadog, slackclient, splunk
    "requests",
    "urllib3",
    "idna",
    "charset_normalizer",
    "certifi",
    # used by splunk mailer transport
    "jsonpointer",
    "jsonpatch",
    # sendgrid dependencies
    "sendgrid",
    "python_http_client",
    "ecdsa",
]


def get_tags(force_deploy=False):
    """Generate all tags for mailer.

    Args:
        force_deploy: Boolean indicating if force deployment is enabled
        version: The c7n-mailer version

    Returns:
        dict: Combined dictionary of all tags
    """
    tags = {}
    tags.update(get_force_deploy_tags(force_deploy))
    return tags


def add_tags_to_mailer(mailer_config, tags):
    """Add tags to mailer config lambda_tags.

    Args:
        mailer_config: Mailer configuration dictionary
        tags: Dict of custodian tags to merge with user's lambda_tags

    Returns:
        dict: Mailer config with tags added to lambda_tags
    """
    if "lambda_tags" not in mailer_config:
        mailer_config["lambda_tags"] = {}

    mailer_config["lambda_tags"].update(tags)

    return mailer_config


def process_lambda_package(query):
    """Process the lambda package creation.

    Args:
        query: Query dictionary

    Returns:
        dict: Result dictionary with information about the zip file
    """
    mailer_config = validate_format(query, "mailer_config")

    tags = get_tags(query.get("force_deploy", "false").lower() == "true")
    mailer_config = add_tags_to_mailer(mailer_config, tags)

    try:
        archive = get_archive(mailer_config)
    except OSError as e:
        raise RuntimeError(f"Failed to create mailer archive due to file system error: {e}")
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Unexpected error creating custodian archive: {type(e).__name__}: {e}")

    try:
        base64_hash = archive.get_checksum()
        hex_hash = archive.get_checksum(encoder=hex_ascii_encoder, hasher=hashlib.sha256)
    except AssertionError as e:
        raise RuntimeError(f"Failed to calculate archive checksums: {e}")

    final_zip_path = copy_archive(archive, hex_hash, query["lambda_name"])
    archive.remove()

    try:
        package_versions = get_package_versions(["c7n-mailer"])
    except Exception as e:  # pragma: no cover
        package_versions = {"error": f"Failed to get package versions: {e}"}

    return {
        "sha256_hex": hex_hash,
        "sha256_base64": base64_hash,
        "zip_path": final_zip_path,
        "package_versions": json.dumps(package_versions),
        "custodian_tags": json.dumps(tags),
    }


def main():
    try:
        query = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        return_error(f"Failed to parse input JSON: {e}")
    except Exception as e:  # pragma: no cover
        return_error(f"Unexpected error reading input: {type(e).__name__}: {e}")

    required = ["mailer_config", "lambda_name"]
    missing = [field for field in required if not query.get(field)]
    if missing:
        return_error(f"Missing required fields: {', '.join(missing)}")

    try:
        result = process_lambda_package(query)
        return_result(result)
    except RuntimeError as e:
        return_error(f"Failed to package lambda: {e}")


if __name__ == "__main__":
    main()  # pragma: no cover
