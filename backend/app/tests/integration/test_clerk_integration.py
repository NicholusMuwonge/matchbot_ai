"""
Integration tests for ClerkService usage in the application
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.clerk_auth import ClerkAuthenticationError


class TestClerkServiceIntegration:
    """Test how ClerkService integrates with other application components"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_auth_route_uses_clerk_service_for_session_validation(self, client):
        """Test that auth routes properly use ClerkService for session validation"""
        with patch("app.api.routes.auth.ClerkService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.validate_session_token.return_value = {
                "user_id": "user_123",
                "expires_at": 1234567890,
            }

            response = client.post(
                "/api/v1/auth/validate-session", json={"session_token": "sess_test123"}
            )

            # Verify ClerkService was instantiated and called
            mock_service_class.assert_called_once()
            mock_service.validate_session_token.assert_called_once_with("sess_test123")

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["clerk_user_id"] == "user_123"

    def test_auth_route_handles_clerk_authentication_error(self, client):
        """Test that auth routes handle ClerkAuthenticationError properly"""
        with patch("app.api.routes.auth.ClerkService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.validate_session_token.side_effect = ClerkAuthenticationError(
                "Invalid token"
            )

            response = client.post(
                "/api/v1/auth/validate-session", json={"session_token": "invalid_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert data["error"] == "Invalid token"

    def test_user_sync_service_uses_clerk_service(self):
        """Test that UserSyncService properly uses ClerkService"""
        with patch("app.services.user_sync_service.ClerkService") as mock_clerk_service:
            mock_clerk = MagicMock()
            mock_clerk_service.return_value = mock_clerk
            mock_clerk.get_user.return_value = {
                "id": "user_123",
                "email": "test@example.com",
                "first_name": "John",
                "last_name": "Doe",
            }

            from app.services.user_sync_service import UserSyncService

            # UserSyncService should instantiate ClerkService in __init__
            sync_service = UserSyncService()

            # Verify ClerkService was instantiated
            mock_clerk_service.assert_called_once()
            assert sync_service.clerk_service is not None

    # TODO: This test is outdated - auth endpoints no longer use UserSyncService directly
    def _test_current_user_endpoint_uses_clerk_service_and_sync_service(self, client):
        """Test that get current user endpoint uses both ClerkService and UserSyncService"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                # Mock Clerk service
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

                # Mock sync service with AsyncMock for async methods
                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync
                mock_sync.fetch_and_sync_user = AsyncMock(
                    return_value={
                        "status": "updated",
                        "user_id": "1",
                        "clerk_user_id": "user_123",
                        "action": "user_updated",
                    }
                )

                response = client.get(
                    "/api/v1/auth/me", headers={"authorization": "Bearer sess_test123"}
                )

                # Verify both services were used
                mock_clerk_service.assert_called_once()
                mock_sync_service.assert_called_once()
                mock_clerk.validate_session_token.assert_called_once()
                mock_sync.fetch_and_sync_user.assert_called_once_with("user_123")

                assert response.status_code == 200

    def test_webhook_handler_uses_clerk_service_for_verification(self, client):
        """Test that webhook handlers use ClerkService for signature verification"""
        with patch("app.webhooks.clerk_webhooks.ClerkService") as mock_clerk_service:
            mock_clerk = MagicMock()
            mock_clerk_service.return_value = mock_clerk
            mock_clerk.verify_webhook_signature.return_value = True

            payload = {"type": "user.created", "data": {"id": "user_123"}}
            headers = {
                "svix-id": "msg_123",
                "svix-timestamp": "1234567890",
                "svix-signature": "v1,test_signature",
            }

            # Use the webhook endpoint directly
            response = client.post(
                "/api/v1/webhooks/clerk", json=payload, headers=headers
            )

            # Verify ClerkService was used for verification
            assert response.status_code == 200
            mock_clerk_service.assert_called_once()

            # Verify that verify_webhook_signature was called with a JSON payload
            mock_clerk.verify_webhook_signature.assert_called_once()
            call_args = mock_clerk.verify_webhook_signature.call_args

            # Check that the first argument (payload) is a JSON string with correct content
            import json

            actual_payload = call_args[0][0]
            actual_headers = call_args[0][1]

            assert json.loads(actual_payload) == payload
            assert actual_headers == headers

    def test_task_system_integration_with_clerk_service(self):
        """Test that Celery tasks integrate properly with ClerkService"""
        with patch("app.services.clerk_auth.ClerkService") as mock_clerk_service:
            from asyncio import Future

            mock_clerk = MagicMock()
            mock_clerk_service.return_value = mock_clerk

            # Create a future for the async get_user call
            future = Future()
            future.set_result(
                {
                    "id": "user_123",
                    "email": "test@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            )
            mock_clerk.get_user.return_value = future

            with patch(
                "app.services.user_sync_service.UserSyncService"
            ) as mock_sync_service:
                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync

                # Create a future for the async sync_user_from_clerk call
                sync_future = Future()
                sync_future.set_result({"status": "success", "user_id": "user_123"})
                mock_sync.sync_user_from_clerk.return_value = sync_future

                from app.tasks.user_sync_tasks import fetch_and_sync_user_task

                # Execute the task (this will run synchronously in test mode)
                fetch_and_sync_user_task.apply(args=["user_123"])

                # Verify ClerkService was used in the task (may be called multiple times due to retries)
                assert mock_clerk_service.call_count >= 1
                mock_clerk.get_user.assert_called_with("user_123")

    def test_clerk_service_error_propagation(self, client):
        """Test that ClerkService errors propagate correctly through the application stack"""
        with patch("app.api.routes.auth.ClerkService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service

            # Simulate different types of ClerkService errors
            mock_service.validate_session_token.side_effect = ClerkAuthenticationError(
                "API key invalid"
            )

            response = client.get(
                "/api/v1/auth/me", headers={"authorization": "Bearer invalid_token"}
            )

            # Application should handle error gracefully
            assert response.status_code == 401
            assert "Request is not authenticated" in response.json()["detail"]

    def test_clerk_service_dependency_injection_pattern(self):
        """Test that services can be properly dependency injected with ClerkService"""
        # This tests the architectural pattern where ClerkService is injected
        # rather than directly instantiated

        with patch("app.services.clerk_auth.clerk_service.Clerk"):
            with patch("os.getenv", return_value="sk_test_123"):
                from app.services.clerk_auth import ClerkService
                from app.services.user_sync_service import UserSyncService

                # Create a ClerkService instance
                clerk_service = ClerkService()

                # In a real DI pattern, we'd inject this into UserSyncService
                # For now, verify the pattern works by checking initialization
                sync_service = UserSyncService()

                # Both should be properly initialized
                assert clerk_service is not None
                assert sync_service is not None
                assert hasattr(sync_service, "clerk_service")


class TestClerkServiceUsagePatterns:
    """Test common usage patterns of ClerkService in the application"""

    def test_service_instantiation_pattern(self):
        """Test the pattern used throughout the app for ClerkService instantiation"""
        # Pattern used in auth.py routes: clerk_service = ClerkService()

        with patch("app.services.clerk_auth.clerk_service.Clerk") as mock_clerk:
            with patch("os.getenv", return_value="sk_test_123"):
                from app.services.clerk_auth import ClerkService

                # This is the pattern used in the actual application
                clerk_service = ClerkService()

                # Verify initialization follows expected pattern
                mock_clerk.assert_called_once()
                assert clerk_service is not None

    # TODO: This test is outdated - validate_session_token method no longer exists
    def _test_error_handling_pattern(self):
        """Test the error handling pattern used with ClerkService"""
        # Pattern used throughout the app: try/except with ClerkAuthenticationError

        with patch("app.services.clerk_auth.clerk_service.Clerk") as mock_clerk:
            with patch("os.getenv", return_value="sk_test_123"):
                from app.services.clerk_auth import (
                    ClerkAuthenticationError,
                    ClerkService,
                )

                clerk_service = ClerkService()
                mock_clerk.return_value.sessions.get.side_effect = Exception(
                    "API Error"
                )

                # This is the pattern used in the actual application
                try:
                    clerk_service.validate_session_token("invalid_token")
                    raise AssertionError("Should have raised ClerkAuthenticationError")
                except ClerkAuthenticationError as e:
                    # Expected behavior
                    assert "Session validation failed" in str(e)

    def test_dependency_injection_with_user_sync_service(self):
        """Test how ClerkService is used as a dependency in UserSyncService"""
        with patch("app.services.clerk_auth.clerk_service.Clerk"):
            with patch("os.getenv", return_value="sk_test_123"):
                from app.services.user_sync_service import UserSyncService

                # UserSyncService creates its own ClerkService instance
                sync_service = UserSyncService()

                # Verify the dependency is properly set up
                assert hasattr(sync_service, "clerk_service")
                assert sync_service.clerk_service is not None
