import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_clerk_test_env():
    original_values = {}

    test_env_vars = {
        "CLERK_SECRET_KEY": "sk_test_mock_key_for_testing",
        "CLERK_PUBLISHABLE_KEY": "pk_test_mock_key_for_testing",
        "CLERK_WEBHOOK_SECRET": "whsec_test_mock_secret_for_testing",
        "CLERK_DEBUG": "false",
    }

    for key, value in test_env_vars.items():
        original_values[key] = os.getenv(key)
        os.environ[key] = value

    yield

    for key, original_value in original_values.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
