"""
Tests for ClerkService using real Clerk SDK structures
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.clerk_auth import ClerkAuthenticationError, ClerkService


@pytest.fixture
def clerk_service():
    """Setup ClerkService instance for testing"""
    with patch("app.services.clerk_auth.clerk_service.Clerk"):
        with patch("os.getenv", return_value="sk_test_mock_key"):
            return ClerkService()


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
    session.last_active_at = int(datetime.utcnow().timestamp()) - 300  # 5 min ago
    session.expire_at = int(datetime.utcnow().timestamp()) + 3600  # 1 hour from now
    session.abandon_at = int(datetime.utcnow().timestamp()) + 7200  # 2 hours from now
    session.created_at = int(datetime.utcnow().timestamp()) - 600  # 10 min ago
    session.updated_at = int(datetime.utcnow().timestamp()) - 300  # 5 min ago

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
    user.created_at = int(datetime.utcnow().timestamp())  # May not exist in real model
    user.updated_at = int(datetime.utcnow().timestamp())  # May not exist in real model

    return user


@pytest.fixture
def mock_user_list():
    """Mock list of users for testing"""
    from clerk_backend_api.models.emailaddress import EmailAddress
    from clerk_backend_api.models.user import User

    # Create mock email and user
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
    user.created_at = int(datetime.utcnow().timestamp())

    return [user]


class TestClerkService:
    """Test ClerkService with actual SDK structures"""

    def test_init_with_valid_keys(self):
        """Test service initialization with valid API keys"""
        with patch("app.services.clerk_auth.clerk_service.Clerk") as mock_clerk:
            with patch("os.getenv", return_value="sk_test_123"):
                service = ClerkService()
                mock_clerk.assert_called_once_with(bearer_auth="sk_test_123")

    def test_init_missing_secret_key_raises_error(self):
        """Test service initialization fails without secret key"""
        with patch("os.getenv", return_value=None):
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.CLERK_SECRET_KEY = None

                with pytest.raises(
                    ClerkAuthenticationError, match="CLERK_SECRET_KEY is required"
                ):
                    ClerkService()

    @pytest.mark.anyio
    async def test_validate_session_token_success(
        self, clerk_service, mock_clerk_session
    ):
        """Test successful session token validation"""
        with patch.object(
            clerk_service.client.sessions, "get", return_value=mock_clerk_session
        ):
            result = await clerk_service.validate_session_token("sess_abc123")

            assert result["valid"] is True
            assert result["session_id"] == "sess_abc123"
            assert result["user_id"] == "user_2abc123def456"
            assert result["status"] == "active"
            assert isinstance(result["expire_at"], int)
            assert isinstance(result["created_at"], int)

    @pytest.mark.anyio
    async def test_validate_session_token_inactive(self, clerk_service):
        """Test inactive session token validation"""
        # Create session with inactive status
        inactive_session = MagicMock()
        inactive_session.id = "sess_inactive"
        inactive_session.user_id = "user_123"
        inactive_session.status = MagicMock()
        inactive_session.status.value = "expired"  # Not active

        with patch.object(
            clerk_service.client.sessions, "get", return_value=inactive_session
        ):
            with pytest.raises(
                ClerkAuthenticationError, match="Session is not active: expired"
            ):
                await clerk_service.validate_session_token("sess_inactive")

    @pytest.mark.anyio
    async def test_validate_session_token_not_found(self, clerk_service):
        """Test session token not found"""
        from clerk_backend_api import SDKError

        # Create proper SDKError with response object
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Session not found"

        with patch.object(
            clerk_service.client.sessions,
            "get",
            side_effect=SDKError("Session not found", mock_response),
        ):
            with pytest.raises(
                ClerkAuthenticationError, match="Session token has expired"
            ):
                await clerk_service.validate_session_token("invalid_token")

    @pytest.mark.anyio
    async def test_get_user_success(self, clerk_service, mock_clerk_user):
        """Test successful user retrieval"""
        with patch.object(
            clerk_service.client.users, "get", return_value=mock_clerk_user
        ):
            result = await clerk_service.get_user("user_2abc123def456")

            assert result["id"] == "user_2abc123def456"
            assert result["email"] == "test@example.com"
            assert result["first_name"] == "John"
            assert result["last_name"] == "Doe"
            assert result["has_image"] is True

    @pytest.mark.anyio
    async def test_get_user_no_primary_email(self, clerk_service):
        """Test user with email but no primary email set"""
        from clerk_backend_api.models.emailaddress import EmailAddress
        from clerk_backend_api.models.user import User

        # Create user with email but no primary_email_address_id match
        email_obj = MagicMock(spec=EmailAddress)
        email_obj.id = "different_id"
        email_obj.email_address = "fallback@example.com"

        user = MagicMock(spec=User)
        user.id = "user_no_primary"
        user.first_name = "Test"
        user.last_name = "User"
        user.primary_email_address_id = "non_matching_id"
        user.email_addresses = [email_obj]
        user.has_image = False

        with patch.object(clerk_service.client.users, "get", return_value=user):
            result = await clerk_service.get_user("user_no_primary")

            # Should fallback to first email in list
            assert result["email"] == "fallback@example.com"

    @pytest.mark.anyio
    async def test_get_user_not_found(self, clerk_service):
        """Test user not found scenario"""
        from clerk_backend_api import SDKError

        # Create proper SDKError
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "User not found"

        with patch.object(
            clerk_service.client.users,
            "get",
            side_effect=SDKError("User not found", mock_response),
        ):
            result = await clerk_service.get_user("nonexistent_user")
            assert result is None

    @pytest.mark.anyio
    async def test_list_users_success(self, clerk_service, mock_user_list):
        """Test successful users listing"""
        with patch.object(
            clerk_service.client.users, "list", return_value=mock_user_list
        ):
            result = await clerk_service.list_users(limit=10)

            assert result["total_count"] == 1
            assert len(result["data"]) == 1
            assert result["data"][0]["id"] == "user_456"
            assert result["data"][0]["email"] == "jane@example.com"
            assert result["data"][0]["has_image"] is False

    @pytest.mark.anyio
    async def test_list_users_with_email_filter(self, clerk_service, mock_user_list):
        """Test users listing with email filter"""
        # Mock the request object creation and SDK call
        with patch(
            "app.services.clerk_auth.clerk_service.GetUserListRequest"
        ) as mock_request_class:
            mock_request = MagicMock()
            mock_request_class.return_value = mock_request

            with patch.object(
                clerk_service.client.users, "list", return_value=mock_user_list
            ):
                result = await clerk_service.list_users(email="jane")

                # Verify request was created with email filter
                mock_request_class.assert_called_once()
                assert mock_request.email_address_query == "jane"

                # Verify results
                assert len(result["data"]) == 1

    @pytest.mark.anyio
    async def test_list_users_empty_result(self, clerk_service):
        """Test users listing with no results"""
        with patch.object(clerk_service.client.users, "list", return_value=None):
            result = await clerk_service.list_users()

            assert result["data"] == []
            assert result["total_count"] == 0

    def test_verify_webhook_signature_success(self, clerk_service):
        """Test successful webhook signature verification"""
        payload = '{"test": "data"}'
        headers = {
            "svix-id": "msg_123",
            "svix-timestamp": str(int(datetime.utcnow().timestamp())),
            "svix-signature": "v1,valid_signature_here",
        }

        # Mock HMAC comparison to return True
        with patch("hmac.compare_digest", return_value=True):
            with patch("os.getenv") as mock_getenv:

                def getenv_side_effect(key, default=None):
                    if key == "CLERK_WEBHOOK_SECRET":
                        return "whsec_test_secret"
                    elif key == "CLERK_SECRET_KEY":
                        return "sk_test_123"
                    return default

                mock_getenv.side_effect = getenv_side_effect

                result = clerk_service.verify_webhook_signature(payload, headers)
                assert result is True

    def test_verify_webhook_signature_missing_headers(self, clerk_service):
        """Test webhook signature verification with missing headers"""
        payload = '{"test": "data"}'
        headers = {}  # Missing required headers

        with patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key, default=None):
                if key == "CLERK_WEBHOOK_SECRET":
                    return "whsec_test_secret"
                elif key == "CLERK_SECRET_KEY":
                    return "sk_test_123"
                return default

            mock_getenv.side_effect = getenv_side_effect

            result = clerk_service.verify_webhook_signature(payload, headers)
            assert result is False

    def test_verify_webhook_signature_expired_timestamp(self, clerk_service):
        """Test webhook signature verification with expired timestamp"""
        payload = '{"test": "data"}'
        # Timestamp from 10 minutes ago (beyond 5 minute window)
        old_timestamp = int(datetime.utcnow().timestamp()) - 600
        headers = {
            "svix-id": "msg_123",
            "svix-timestamp": str(old_timestamp),
            "svix-signature": "v1,signature_here",
        }

        with patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key, default=None):
                if key == "CLERK_WEBHOOK_SECRET":
                    return "whsec_test_secret"
                elif key == "CLERK_SECRET_KEY":
                    return "sk_test_123"
                return default

            mock_getenv.side_effect = getenv_side_effect

            result = clerk_service.verify_webhook_signature(payload, headers)
            assert result is False
