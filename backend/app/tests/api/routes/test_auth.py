"""
Tests for authentication routes
"""

from unittest.mock import MagicMock, patch


class TestAuthRoutes:
    """Test authentication endpoints"""

    def test_validate_session_success(self, client):
        """Test successful session validation"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            mock_clerk = MagicMock()
            mock_clerk_service.return_value = mock_clerk
            mock_clerk.validate_session_token.return_value = {
                "valid": True,
                "user_id": "user_123",
                "expires_at": 1234567890,
            }

            response = client.post(
                "/api/v1/auth/validate-session", json={"session_token": "sess_test123"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["user_id"] == "user_123"
            assert data["clerk_user_id"] == "user_123"

    def test_validate_session_invalid(self, client):
        """Test session validation with invalid token"""
        with patch("app.api.routes.auth.ClerkService") as mock_clerk_service:
            mock_clerk = MagicMock()
            mock_clerk_service.return_value = mock_clerk
            from app.services.clerk_auth import ClerkAuthenticationError

            mock_clerk.validate_session_token.side_effect = ClerkAuthenticationError(
                "Invalid session token"
            )

            response = client.post(
                "/api/v1/auth/validate-session", json={"session_token": "invalid_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert "Invalid session token" in data["error"]

    def test_get_current_user_missing_auth(self, client):
        """Test get current user without authorization header"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "Request is not authenticated" in response.json()["detail"]

    def test_get_current_user_invalid_bearer(self, client):
        """Test get current user with invalid bearer format"""
        response = client.get(
            "/api/v1/auth/me", headers={"authorization": "InvalidFormat"}
        )

        assert response.status_code == 401
        assert "Request is not authenticated" in response.json()["detail"]

    # TODO: Fix this test - it needs proper FastAPI dependency injection mocking
    # def test_get_current_user_success(self, client):
    #     """Test successful current user retrieval"""
    #     pass

    # TODO: sync-user endpoints no longer exist, moved to users routes
    # Additional tests should be added to cover the /users/clerk/* endpoints
