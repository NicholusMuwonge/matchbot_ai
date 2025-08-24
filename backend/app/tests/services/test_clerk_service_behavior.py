"""
Tests for ClerkService behavior and integration - Properly grouped by context
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.clerk_auth import ClerkAuthenticationError, ClerkService


class TestClerkServiceInitialization:
    """Context: Service initialization behavior"""

    class TestWithoutApiKey:
        """Context: When API key is not available"""

        @pytest.fixture(autouse=True)
        def setup_no_api_key(self):
            """Setup: No API key available"""
            with patch("os.getenv", return_value=None):
                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.CLERK_SECRET_KEY = None
                    yield

        def test_raises_authentication_error(self):
            """Should raise ClerkAuthenticationError when no API key"""
            with pytest.raises(
                ClerkAuthenticationError, match="CLERK_SECRET_KEY is required"
            ):
                ClerkService()

    class TestWithApiKey:
        """Context: When API key is available"""

        @pytest.fixture(autouse=True)
        def setup_with_api_key(self):
            """Setup: API key available"""
            with patch("app.services.clerk_auth.clerk_service.Clerk") as mock_clerk:
                with patch("os.getenv", return_value="sk_test_123"):
                    with patch("app.services.clerk_auth.clerk_service.logging"):
                        self.mock_clerk = mock_clerk
                        yield

        def test_initializes_successfully(self):
            """Should initialize successfully with API key"""
            service = ClerkService()
            assert service is not None

        def test_includes_debug_logger_parameter(self):
            """Should include debug_logger parameter in Clerk SDK initialization"""
            ClerkService()

            # Verify Clerk was called with correct parameters
            assert self.mock_clerk.call_count == 1
            call_args = self.mock_clerk.call_args
            assert call_args[1]["bearer_auth"] == "sk_test_123"
            # Should have debug_logger parameter (can be None)
            assert "debug_logger" in call_args[1]


class TestClerkServiceSessionValidation:
    """Context: Session token validation with valid service"""

    def test_success_returns_expected_data(self, clerk_service, mock_clerk_session):
        """Should return session data when token is valid"""
        with patch.object(
            clerk_service.client.sessions, "get", return_value=mock_clerk_session
        ):
            result = clerk_service.validate_session_token("sess_abc123")

            assert result["valid"] is True
            assert result["session_id"] == "sess_abc123"
            assert result["user_id"] == "user_2abc123def456"
            assert result["status"] == "active"
            assert isinstance(result["expire_at"], int)
            assert isinstance(result["created_at"], int)

    def test_inactive_session_raises_error(self, clerk_service):
        """Should raise error when session is not active"""
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
                clerk_service.validate_session_token("sess_inactive")

    def test_not_found_raises_appropriate_error(self, clerk_service):
        """Should raise appropriate error when session not found"""
        from clerk_backend_api import SDKError

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
                clerk_service.validate_session_token("invalid_token")


class TestClerkServiceUserRetrieval:
    """Context: User data retrieval from Clerk with valid service"""

    def test_success_returns_formatted_data(self, clerk_service, mock_clerk_user):
        """Should return properly formatted user data when user exists"""
        with patch.object(
            clerk_service.client.users, "get", return_value=mock_clerk_user
        ):
            result = clerk_service.get_user("user_2abc123def456")

            assert result["id"] == "user_2abc123def456"
            assert result["email"] == "test@example.com"
            assert result["first_name"] == "John"
            assert result["last_name"] == "Doe"
            assert result["has_image"] is True

    def test_email_fallback_when_no_primary_match(self, clerk_service):
        """Should fallback to first email when no primary email matches"""
        from clerk_backend_api.models.emailaddress import EmailAddress
        from clerk_backend_api.models.user import User

        # Create user with email but no matching primary_email_address_id
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
            result = clerk_service.get_user("user_no_primary")

            # Should fallback to first email in list
            assert result["email"] == "fallback@example.com"

    def test_not_found_returns_none(self, clerk_service):
        """Should return None when user not found instead of raising error"""
        from clerk_backend_api import SDKError

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "User not found"

        with patch.object(
            clerk_service.client.users,
            "get",
            side_effect=SDKError("User not found", mock_response),
        ):
            result = clerk_service.get_user("nonexistent_user")
            assert result is None


class TestClerkServiceUserListing:
    """Context: Listing users from Clerk with valid service"""

    def test_success_returns_formatted_data(self, clerk_service, mock_user_list):
        """Should return properly formatted user list when users exist"""
        with patch.object(
            clerk_service.client.users, "list", return_value=mock_user_list
        ):
            result = clerk_service.list_users(limit=10)

            assert result["total_count"] == 1
            assert len(result["data"]) == 1
            assert result["data"][0]["id"] == "user_456"
            assert result["data"][0]["email"] == "jane@example.com"
            assert result["data"][0]["has_image"] is False

    def test_with_email_filter_creates_proper_request(
        self, clerk_service, mock_user_list
    ):
        """Should create proper request with email filter"""
        with patch(
            "app.services.clerk_auth.clerk_service.GetUserListRequest"
        ) as mock_request_class:
            mock_request = MagicMock()
            mock_request_class.return_value = mock_request

            with patch.object(
                clerk_service.client.users, "list", return_value=mock_user_list
            ):
                result = clerk_service.list_users(email="jane")

                # Verify request was created with email filter
                mock_request_class.assert_called_once()
                assert mock_request.email_address_query == "jane"

                # Verify results
                assert len(result["data"]) == 1

    def test_empty_result_handled_gracefully(self, clerk_service):
        """Should handle empty results gracefully"""
        with patch.object(clerk_service.client.users, "list", return_value=None):
            result = clerk_service.list_users()

            assert result["data"] == []
            assert result["total_count"] == 0


class TestClerkServiceWebhookSignatureVerification:
    """Context: Webhook signature verification with valid service"""

    @pytest.fixture(autouse=True)
    def setup_webhook_environment(self):
        """Setup: Environment for webhook testing"""
        with patch("os.getenv") as mock_getenv:

            def getenv_side_effect(key, default=None):
                if key == "CLERK_WEBHOOK_SECRET":
                    return "whsec_test_secret"
                elif key == "CLERK_SECRET_KEY":
                    return "sk_test_123"
                return default

            mock_getenv.side_effect = getenv_side_effect
            yield

    def test_success_with_valid_signature(self, clerk_service):
        """Should return True when webhook signature is valid"""
        payload = '{"test": "data"}'
        headers = {
            "svix-id": "msg_123",
            "svix-timestamp": str(int(datetime.utcnow().timestamp())),
            "svix-signature": "v1,valid_signature_here",
        }

        # Mock HMAC comparison to return True
        with patch("hmac.compare_digest", return_value=True):
            result = clerk_service.verify_webhook_signature(payload, headers)
            assert result is True

    def test_failure_with_missing_headers(self, clerk_service):
        """Should return False when required headers are missing"""
        payload = '{"test": "data"}'
        headers = {}  # Missing required headers

        result = clerk_service.verify_webhook_signature(payload, headers)
        assert result is False

    def test_failure_with_expired_timestamp(self, clerk_service):
        """Should return False when timestamp is expired"""
        payload = '{"test": "data"}'
        # Timestamp from 10 minutes ago (beyond 5 minute window)
        old_timestamp = int(datetime.utcnow().timestamp()) - 600
        headers = {
            "svix-id": "msg_123",
            "svix-timestamp": str(old_timestamp),
            "svix-signature": "v1,signature_here",
        }

        result = clerk_service.verify_webhook_signature(payload, headers)
        assert result is False
