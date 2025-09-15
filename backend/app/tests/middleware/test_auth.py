"""
Tests for Authentication Middleware

Tests the authentication middleware that validates JWT tokens via Clerk.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.middleware.auth import AuthMiddleware
from app.services.clerk_auth import ClerkAuthenticationError


@pytest.fixture
def mock_app():
    """Create a mock FastAPI app."""
    return MagicMock()


@pytest.fixture
def auth_middleware(mock_app):
    """Create an instance of AuthMiddleware."""
    return AuthMiddleware(mock_app)


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/users"
    request.method = "GET"
    request.state = MagicMock()
    request.headers = {}
    return request


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function."""

    async def call_next(request):  # noqa: ARG001
        return JSONResponse({"message": "success"}, status_code=200)

    return call_next


class TestAuthMiddleware:
    """Test cases for AuthMiddleware."""

    @pytest.mark.asyncio
    async def test_public_path_skipped(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that public paths skip authentication."""
        mock_request.url.path = "/docs"

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        # Should not have auth data set
        assert not hasattr(mock_request.state, "auth_data")

    @pytest.mark.asyncio
    async def test_options_request_skipped(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that OPTIONS requests skip authentication."""
        mock_request.method = "OPTIONS"

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth.ClerkService")
    async def test_valid_token_authentication(
        self, mock_clerk_service, auth_middleware, mock_request, mock_call_next
    ):
        """Test successful authentication with valid token."""
        # Setup mock
        mock_clerk_instance = MagicMock()
        mock_clerk_service.return_value = mock_clerk_instance
        mock_clerk_instance.get_enhanced_auth_data.return_value = {
            "valid": True,
            "is_signed_in": True,
            "authenticated": True,
            "user_id": "user_123",
            "user_role": "admin",
            "is_app_owner": False,
            "token_claims": {"role": "admin"},
        }

        # Add auth header
        mock_request.headers = {"authorization": "Bearer valid_token"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert mock_request.state.authenticated is True
        assert mock_request.state.auth_data["user_id"] == "user_123"
        assert mock_request.state.user_id == "user_123"

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth.ClerkService")
    async def test_invalid_token_authentication(
        self, mock_clerk_service, auth_middleware, mock_request, mock_call_next
    ):
        """Test failed authentication with invalid token."""
        # Setup mock to raise authentication error
        mock_clerk_instance = MagicMock()
        mock_clerk_service.return_value = mock_clerk_instance
        mock_clerk_instance.get_enhanced_auth_data.side_effect = (
            ClerkAuthenticationError("Invalid token")
        )

        # Add auth header
        mock_request.headers = {"authorization": "Bearer invalid_token"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert (
            response.status_code == 200
        )  # Middleware doesn't block, just marks as unauthenticated
        assert mock_request.state.authenticated is False
        assert mock_request.state.auth_data is None
        assert mock_request.state.auth_error == "Invalid token"

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth.ClerkService")
    async def test_missing_authorization_header(
        self, mock_clerk_service, auth_middleware, mock_request, mock_call_next
    ):
        """Test request without authorization header."""
        # Setup mock to raise authentication error
        mock_clerk_instance = MagicMock()
        mock_clerk_service.return_value = mock_clerk_instance
        mock_clerk_instance.get_enhanced_auth_data.side_effect = (
            ClerkAuthenticationError("Missing or invalid Authorization header")
        )

        # No auth header
        mock_request.headers = {}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert mock_request.state.authenticated is False
        assert mock_request.state.auth_data is None

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth.ClerkService")
    async def test_expired_token(
        self, mock_clerk_service, auth_middleware, mock_request, mock_call_next
    ):
        """Test authentication with expired token."""
        # Setup mock
        mock_clerk_instance = MagicMock()
        mock_clerk_service.return_value = mock_clerk_instance
        mock_clerk_instance.get_enhanced_auth_data.side_effect = (
            ClerkAuthenticationError("TokenVerificationErrorReason.TOKEN_EXPIRED")
        )

        # Add auth header
        mock_request.headers = {"authorization": "Bearer expired_token"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert mock_request.state.authenticated is False
        assert "TOKEN_EXPIRED" in mock_request.state.auth_error

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth.ClerkService")
    async def test_app_owner_role_extraction(
        self, mock_clerk_service, auth_middleware, mock_request, mock_call_next
    ):
        """Test that app_owner role is correctly extracted from token."""
        # Setup mock
        mock_clerk_instance = MagicMock()
        mock_clerk_service.return_value = mock_clerk_instance
        mock_clerk_instance.get_enhanced_auth_data.return_value = {
            "valid": True,
            "is_signed_in": True,
            "authenticated": True,
            "user_id": "user_123",
            "user_role": "app_owner",
            "is_app_owner": True,
            "token_claims": {"role": "app_owner", "isAppOwner": True},
        }

        # Add auth header
        mock_request.headers = {"authorization": "Bearer app_owner_token"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert mock_request.state.auth_data["user_role"] == "app_owner"
        assert mock_request.state.auth_data["is_app_owner"] is True

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth.ClerkService")
    async def test_unexpected_error_handling(
        self, mock_clerk_service, auth_middleware, mock_request, mock_call_next
    ):
        """Test handling of unexpected errors during authentication."""
        # Setup mock to raise unexpected error
        mock_clerk_instance = MagicMock()
        mock_clerk_service.return_value = mock_clerk_instance
        mock_clerk_instance.get_enhanced_auth_data.side_effect = Exception(
            "Unexpected error"
        )

        # Add auth header
        mock_request.headers = {"authorization": "Bearer some_token"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200
        assert mock_request.state.authenticated is False
        assert mock_request.state.auth_data is None
        assert "Auth system error" in mock_request.state.auth_error
