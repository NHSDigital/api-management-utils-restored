"""
TLDR: A simple regex matches my intuitions.
"""

from ansible_collections.nhsd.apigee.plugins.module_utils.models.ansible.validate_manifest import (
    correct_namespace
)


API_NAME = "canary-api"
ENV_NAME = "internal-dev"


def test_correct_namespace_no_suffixes():
    assert correct_namespace("canary-api-internal-dev", API_NAME, ENV_NAME) is True


def test_correct_namespace_with_api_name_suffix():
    assert correct_namespace("canary-api-suffix-internal-dev", API_NAME, ENV_NAME) is True


def test_correct_namespace_with_env_name_suffix():
    assert correct_namespace("canary-api-internal-dev-application-restricted", API_NAME, ENV_NAME) is True


def test_correct_namespace_with_both_types_of_suffix():
    assert correct_namespace("canary-api-suffix-internal-dev-application-restricted", API_NAME, ENV_NAME) is True


def test_correct_namespace_with_number_in_suffix():
    assert correct_namespace("canary-api-suffix1-internal-dev-suffix2", API_NAME, ENV_NAME) is True


def test_correct_namespace_missing_hyphen_1():
    assert correct_namespace("canary-apisuffix-internal-dev-application-restricted", API_NAME, ENV_NAME) is False


def test_correct_namespace_missing_hyphen_2():
    assert correct_namespace("canary-api-suffix-internal-devapplication-restricted", API_NAME, ENV_NAME) is False


def test_correct_namespace_trailing_hyphen():
    assert correct_namespace("canary-api-internal-dev-", API_NAME, ENV_NAME) is False


def test_correct_namespace_wrong_env_name():
    assert correct_namespace("canary-api-internal-qa", API_NAME, ENV_NAME) is False


def test_correct_namespace_wrong_api_name():
    assert correct_namespace("robin-redbrest-api-internal-dev", API_NAME, ENV_NAME) is False
