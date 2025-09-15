import fnmatch
import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """
    Authorization middleware that checks user roles against route requirements.
    Runs after AuthMiddleware which sets request.state.auth_data.
    """

    def __init__(self, app):
        super().__init__(app)
        # Only include routes that NEED authorization
        # Routes not listed here are open to all authenticated users
        # Note: Patterns match both with and without trailing slashes
        self.route_role_mappings = {
            "/api/v1/admin*": ["admin", "app_owner"],
            "/api/v1/users*": ["admin", "app_owner"],
            "/api/v1/teams*": ["team_member", "admin", "app_owner"],
            "/api/v1/items*": ["user", "admin", "app_owner"],
        }

    async def dispatch(self, request: Request, call_next):
        """Process authorization for each request."""
        path = request.url.path
        logger.info(f"💛 AUTHORIZATION: Checking path: {path}")

        # OPTIMIZATION: Early exit for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            logger.debug("💛 AUTHORIZATION: Skipping OPTIONS request")
            return await call_next(request)

        # OPTIMIZATION: Check if route needs authorization FIRST
        required_roles = self._get_required_roles(path)
        logger.info(f"💛 AUTHORIZATION: Required roles for {path}: {required_roles}")

        # No pattern matched = no authorization required, allow through immediately
        if required_roles is None:
            logger.info(f"💛 AUTHORIZATION: No authorization required for {path}")
            return await call_next(request)

        # Check if authentication was successful
        if (
            not hasattr(request.state, "authenticated")
            or not request.state.authenticated
        ):
            logger.info(
                "💛 AUTHORIZATION: Skipping authorization - user not authenticated"
            )
            # Let the request continue - deps.py will handle the 401
            return await call_next(request)

        auth_data = getattr(request.state, "auth_data", None)
        if not auth_data:
            logger.error(
                "💛 AUTHORIZATION: auth_data is None despite authenticated=True"
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Authorization data missing"},
            )
        user_role = auth_data.get("user_role")

        if not self._is_authorized(user_role, required_roles):
            logger.warning(
                f"Access denied for user role '{user_role}' to {path}. "
                f"Required roles: {required_roles}"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": f"Access denied. Required roles: {', '.join(required_roles)}"
                },
            )

        logger.info(f"Access granted for role '{user_role}' to {path}")
        return await call_next(request)

    def _get_required_roles(self, path: str) -> list[str] | None:
        """Find required roles for the given path."""
        for pattern, roles in self.route_role_mappings.items():
            if fnmatch.fnmatch(path, pattern):
                return roles
        return None

    def _is_authorized(self, user_role: str | None, required_roles: list[str]) -> bool:
        """Check if user role is in the list of required roles."""
        if not user_role:
            return False

        # Special case: "*" means any authenticated user
        if "*" in required_roles:
            return True

        return user_role in required_roles
