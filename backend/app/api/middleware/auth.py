import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.clerk_auth import ClerkAuthenticationError, ClerkService

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Simple MVP authentication middleware that does auth check ONCE per request.

    - Does authentication using existing ClerkService.get_enhanced_auth_data()
    - Stores result in request.state for routes to access
    - Skips auth for public paths
    """

    def __init__(self, app):
        super().__init__(app)
        self.unprotected_routes = {"/docs", "/openapi.json", "/redoc", "health-check/"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.unprotected_routes:
            logger.info(
                f"🔥 AuthMiddleware: Skipping auth for public path: {request.url.path}"
            )
            return await call_next(request)

        # Skip auth for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Do auth check ONCE using existing ClerkService
        logger.info(f"🔥 AuthMiddleware: Authenticating request to {request.url.path}")

        try:
            clerk_service = ClerkService()
            auth_data = clerk_service.get_enhanced_auth_data(request)

            request.state.auth_data = auth_data
            request.state.authenticated = True
            request.state.user_id = auth_data.get("user_id")

            logger.info(f"✅ AuthMiddleware: Auth Data {auth_data}")
            logger.info(
                f"✅ AuthMiddleware: Authentication successful for user {auth_data.get('user_id')}"
            )

        except ClerkAuthenticationError as e:
            logger.warning(f"❌ AuthMiddleware: Authentication failed: {str(e)}")
            request.state.auth_data = None
            request.state.authenticated = False
            request.state.auth_error = str(e)

        except Exception as e:
            logger.error(f"❌ AuthMiddleware: Unexpected auth error: {str(e)}")
            request.state.auth_data = None
            request.state.authenticated = False
            request.state.auth_error = f"Auth system error: {str(e)}"

        return await call_next(request)
