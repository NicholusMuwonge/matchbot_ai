"""
Clerk-related test fixtures
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_clerk_session():
    """Mock Clerk Session object based on actual SDK structure"""
    from clerk_backend_api.models.session import Session

    # Create mock session with actual SDK structure
    session = MagicMock(spec=Session)
    session.id = "sess_abc123"
    session.user_id = "user_2abc123def456"
    session.client_id = "client_123"
    session.status = MagicMock()
    session.status.value = "active"  # Enum value
    session.last_active_at = (
        int(datetime.now(timezone.utc).timestamp()) - 300
    )  # 5 min ago
    session.expire_at = (
        int(datetime.now(timezone.utc).timestamp()) + 3600
    )  # 1 hour from now
    session.abandon_at = (
        int(datetime.now(timezone.utc).timestamp()) + 7200
    )  # 2 hours from now
    session.created_at = int(datetime.now(timezone.utc).timestamp()) - 600  # 10 min ago
    session.updated_at = int(datetime.now(timezone.utc).timestamp()) - 300  # 5 min ago

    return session


@pytest.fixture
def mock_clerk_user():
    """Mock Clerk User object based on actual SDK structure"""
    from clerk_backend_api.models.emailaddress import EmailAddress
    from clerk_backend_api.models.user import User

    # Create mock email address
    email_obj = MagicMock(spec=EmailAddress)
    email_obj.id = "idn_email_123"
    email_obj.email_address = "test@example.com"

    # Create mock user with actual SDK structure
    user = MagicMock(spec=User)
    user.id = "user_2abc123def456"
    user.object = MagicMock()
    user.object.value = "user"
    user.first_name = "John"
    user.last_name = "Doe"
    user.has_image = True
    user.image_url = "https://img.clerk.com/test_image"  # May not exist in real model
    user.primary_email_address_id = "idn_email_123"
    user.email_addresses = [email_obj]
    user.created_at = int(
        datetime.now(timezone.utc).timestamp()
    )  # May not exist in real model
    user.updated_at = int(
        datetime.now(timezone.utc).timestamp()
    )  # May not exist in real model

    return user


@pytest.fixture
def mock_user_list():
    """Mock list of users for testing"""
    from clerk_backend_api.models.emailaddress import EmailAddress
    from clerk_backend_api.models.user import User

    email_obj = MagicMock(spec=EmailAddress)
    email_obj.id = "idn_email_456"
    email_obj.email_address = "jane@example.com"

    user = MagicMock(spec=User)
    user.id = "user_456"
    user.first_name = "Jane"
    user.last_name = "Smith"
    user.has_image = False
    user.image_url = None
    user.primary_email_address_id = "idn_email_456"
    user.email_addresses = [email_obj]
    user.created_at = int(datetime.now(timezone.utc).timestamp())

    return [user]


@pytest.fixture
def clerk_service():
    """Setup ClerkService instance for testing with mocked Clerk SDK"""
    from unittest.mock import patch

    with patch("app.services.clerk_auth.clerk_service.Clerk"):
        with patch("os.getenv", return_value="sk_test_mock_key"):
            from app.services.clerk_auth import ClerkService

            return ClerkService()
