"""
Tests for Clerk authentication API routes
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.clerk_auth import ClerkAuthenticationError


class TestAuthRoutes:
    """Test Clerk authentication endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_validate_session_success(self, client):
        """Test successful session validation"""
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

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["clerk_user_id"] == "user_123"
            assert data["expires_at"] == 1234567890
            assert data["error"] is None

    def test_validate_session_invalid(self, client):
        """Test session validation with invalid token"""
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

    def test_get_current_user_missing_auth(self, client):
        """Test get current user without authorization header"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Missing or invalid authorization header" in response.json()["detail"]

    def test_get_current_user_invalid_bearer(self, client):
        """Test get current user with invalid bearer format"""
        response = client.get(
            "/api/v1/auth/me", headers={"authorization": "Invalid token_format"}
        )

        assert response.status_code == 401
        assert "Missing or invalid authorization header" in response.json()["detail"]

    def test_get_current_user_success(self, client):
        """Test successful current user retrieval"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

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

                assert response.status_code == 200
                data = response.json()
                assert data["id"] == 1
                assert data["clerk_user_id"] == "user_123"

    def test_sync_user_missing_auth(self, client):
        """Test user sync without authorization"""
        response = client.post("/api/v1/auth/sync-user/user_123")

        assert response.status_code == 401

    def test_sync_user_success(self, client, db):
        """Test successful user sync"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync
                mock_sync.fetch_and_sync_user = AsyncMock(
                    return_value={
                        "status": "created",
                        "user_id": "1",
                        "clerk_user_id": "user_123",
                        "action": "user_created",
                    }
                )

                response = client.post(
                    "/api/v1/auth/sync-user/user_123",
                    headers={"authorization": "Bearer sess_test123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "created"
                assert data["clerk_user_id"] == "user_123"
                assert data["action"] == "user_created"

    def test_sync_user_not_found(self, client, db):
        """Test user sync when user not found"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync
                mock_sync.fetch_and_sync_user = AsyncMock(
                    return_value={"status": "not_found"}
                )

                response = client.post(
                    "/api/v1/auth/sync-user/user_123",
                    headers={"authorization": "Bearer sess_test123"},
                )

                assert response.status_code == 404
                assert "User not found in Clerk" in response.json()["detail"]

    def test_sync_user_by_email_success(self, client, db):
        """Test successful user sync by email"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                # Mock Clerk service
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

                # Mock sync service with AsyncMock
                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync
                mock_sync.sync_user_by_email = AsyncMock(
                    return_value={
                        "status": "created",
                        "user_id": "1",
                        "clerk_user_id": "user_123",
                        "action": "user_created",
                    }
                )

                response = client.post(
                    "/api/v1/auth/sync-user-by-email?email=test@example.com",
                    headers={"authorization": "Bearer sess_test123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "created"
                assert data["clerk_user_id"] == "user_123"

    def test_sync_user_by_email_not_found(self, client, db):
        """Test user sync by email when user not found"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                # Mock Clerk service
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

                # Mock sync service with AsyncMock
                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync
                mock_sync.sync_user_by_email = AsyncMock(return_value=None)

                response = client.post(
                    "/api/v1/auth/sync-user-by-email?email=notfound@example.com",
                    headers={"authorization": "Bearer sess_test123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "No user found with email" in data["message"]

    def test_get_sync_stats(self, client, db):
        """Test get sync statistics"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            with patch("app.api.routes.auth.UserSyncService") as mock_sync_service:
                mock_clerk = MagicMock()
                mock_clerk_service.return_value = mock_clerk
                mock_clerk.validate_session_token.return_value = {"user_id": "user_123"}

                mock_sync = MagicMock()
                mock_sync_service.return_value = mock_sync
                mock_sync.get_sync_stats.return_value = {
                    "total_users": 100,
                    "synced_users": 85,
                    "unsynced_users": 15,
                    "active_users": 90,
                    "clerk_users": 85,
                }

                response = client.get(
                    "/api/v1/auth/sync-stats",
                    headers={"authorization": "Bearer sess_test123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["total_users"] == 100
                assert data["synced_users"] == 85
                assert data["clerk_users"] == 85
