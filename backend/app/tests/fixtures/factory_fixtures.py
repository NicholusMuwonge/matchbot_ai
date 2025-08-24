import pytest

from app.tests.factories.clerk_factory import ClerkUserDataFactory, ClerkWebhookFactory
from app.tests.factories.user_factory import ClerkUserFactory, UserFactory
from app.tests.factories.webhook_factory import WebhookEventFactory


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def clerk_user_factory():
    return ClerkUserFactory


@pytest.fixture
def webhook_factory():
    return WebhookEventFactory


@pytest.fixture
def clerk_data_factory():
    return ClerkUserDataFactory


@pytest.fixture
def clerk_webhook_factory():
    return ClerkWebhookFactory
