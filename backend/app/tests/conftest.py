from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, User
from app.tests.factories.clerk_factory import ClerkUserDataFactory, ClerkWebhookFactory

# Import factories for pytest-factoryboy registration
from app.tests.factories.user_factory import ClerkUserFactory, UserFactory
from app.tests.factories.webhook_factory import WebhookEventFactory
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


# Factory fixtures (like Ruby Factory Bot)
@pytest.fixture
def user_factory():
    """User factory fixture"""
    return UserFactory


@pytest.fixture
def clerk_user_factory():
    """Clerk user factory fixture"""
    return ClerkUserFactory


@pytest.fixture
def webhook_factory():
    """Webhook factory fixture"""
    return WebhookEventFactory


@pytest.fixture
def clerk_data_factory():
    """Clerk API data factory fixture"""
    return ClerkUserDataFactory


@pytest.fixture
def clerk_webhook_factory():
    """Clerk webhook factory fixture"""
    return ClerkWebhookFactory
