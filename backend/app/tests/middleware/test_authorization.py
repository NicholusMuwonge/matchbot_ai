"""
Tests for Authorization Middleware

Tests the authorization middleware that checks user roles against route requirements.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.middleware.authorization import AuthorizationMiddleware


@pytest.fixture
def mock_app():
    """Create a mock FastAPI app."""
    return MagicMock()


@pytest.fixture
def auth_middleware(mock_app):
    """Create an instance of AuthorizationMiddleware."""
    return AuthorizationMiddleware(mock_app)


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/users"
    request.method = "GET"
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function."""

    async def call_next(request):  # noqa: ARG001
        return JSONResponse({"message": "success"}, status_code=200)

    return call_next


class TestAuthorizationMiddleware:
    """Test cases for AuthorizationMiddleware."""

    @pytest.mark.asyncio
    async def test_options_request_passes_through(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that OPTIONS requests pass through without authorization."""
        mock_request.method = "OPTIONS"

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unprotected_route_passes_through(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that routes not in role_mappings pass through."""
        mock_request.url.path = "/api/v1/unprotected"

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_user_passes_through(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that unauthenticated users are passed to deps for 401 handling."""
        mock_request.url.path = "/api/v1/users"
        mock_request.state.authenticated = False

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        # Should pass through - deps.py will handle 401
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_route(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that admin role can access admin-only routes."""
        mock_request.url.path = "/api/v1/users"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = {"user_role": "admin"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_app_owner_blocked_from_admin_only_route(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that app_owner is blocked from admin-only routes."""
        mock_request.url.path = "/api/v1/users"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = {"user_role": "app_owner"}

        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_app_owner_can_access_shared_route(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that app_owner can access routes that include app_owner role."""
        mock_request.url.path = "/api/v1/admin/dashboard"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = {"user_role": "app_owner"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_wildcard_pattern_matching(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that wildcard patterns match correctly."""
        # Test various paths that should match /api/v1/users*
        test_paths = [
            "/api/v1/users",
            "/api/v1/users/",
            "/api/v1/users/123",
            "/api/v1/users/123/profile",
        ]

        for path in test_paths:
            mock_request.url.path = path
            mock_request.state.authenticated = True
            mock_request.state.auth_data = {"user_role": "admin"}

            response = await auth_middleware.dispatch(mock_request, mock_call_next)
            assert response.status_code == 200, f"Failed for path: {path}"

    @pytest.mark.asyncio
    async def test_missing_auth_data_when_authenticated(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test error handling when auth_data is missing despite authenticated=True."""
        mock_request.url.path = "/api/v1/users"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 500
        assert "Authorization data missing" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_user_without_role(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test that users without any role are denied access."""
        mock_request.url.path = "/api/v1/users"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = {"user_role": None}

        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_team_member_access(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test team_member role access to team routes."""
        mock_request.url.path = "/api/v1/teams/123"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = {"user_role": "team_member"}

        response = await auth_middleware.dispatch(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_team_member_blocked_from_admin(
        self, auth_middleware, mock_request, mock_call_next
    ):
        """Test team_member cannot access admin routes."""
        mock_request.url.path = "/api/v1/admin/settings"
        mock_request.state.authenticated = True
        mock_request.state.auth_data = {"user_role": "team_member"}

        with pytest.raises(HTTPException) as exc_info:
            await auth_middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 403
