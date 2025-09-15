"""
Clerk Service

Handles Clerk authentication and user management operations using the actual SDK.
"""

import logging
import os
import time
from typing import Any

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Request

from app.core.config import settings

logger = logging.getLogger(__name__)


class ClerkAuthenticationError(Exception):
    """Raised when Clerk authentication operations fail"""

    pass


class ClerkService:
    """Clerk service that handles authentication and user management"""

    def __init__(self) -> None:
        """Initialize Clerk client with logging"""
        logger.info("🔥 ClerkService: Starting __init__ method")
        api_key = os.getenv("CLERK_SECRET_KEY") or settings.CLERK_SECRET_KEY
        logger.info(
            f"🔥 ClerkService: Retrieved API key: {'SET' if api_key else 'NOT SET'}"
        )
        if not api_key:
            logger.error("🔥 ClerkService: No API key found - raising error")
            raise ClerkAuthenticationError(
                "CLERK_SECRET_KEY is required for production"
            )

        self.logger = logging.getLogger("clerk_service")

        self.debug = (
            settings.ENVIRONMENT == "local"
            or settings.CLERK_DEBUG
            or os.getenv("CLERK_DEBUG", "").lower() == "true"
        )

        if self.debug:
            clerk_logger = logging.getLogger("clerk_backend_api")
            clerk_logger.setLevel(logging.DEBUG)
        else:
            clerk_logger = logging.getLogger("clerk_backend_api")
            clerk_logger.setLevel(logging.WARNING)

        if api_key:
            self.logger.info(f"🔍 Clerk Init: API key prefix: {api_key[:10]}...")

        try:
            self.client = Clerk(
                bearer_auth=api_key, debug_logger=clerk_logger if self.debug else None
            )
        except Exception as e:
            logger.error(f"🔥 ClerkService: Failed to create SDK client: {e}")
            raise

        self.publishable_key = (
            os.getenv("CLERK_PUBLISHABLE_KEY") or settings.CLERK_PUBLISHABLE_KEY
        )

        self.logger.info(
            f"🔍 Clerk Init: Publishable key present: {bool(self.publishable_key)}"
        )
        if self.publishable_key:
            self.logger.info(
                f"🔍 Clerk Init: Publishable key prefix: {self.publishable_key[:10]}..."
            )

        self.logger.info(
            f"ClerkService initialized for environment: {settings.ENVIRONMENT}"
        )

        try:
            self.logger.info("🔍 Clerk Init: Testing SDK client methods...")
            sdk_methods = [
                method for method in dir(self.client) if not method.startswith("_")
            ]
            self.logger.info(
                f"🔍 Clerk Init: Available SDK methods: {len(sdk_methods)}"
            )
            has_auth_method = hasattr(self.client, "authenticate_request")
            self.logger.info(
                f"🔍 Clerk Init: Has authenticate_request method: {has_auth_method}"
            )
        except Exception as e:
            self.logger.error(f"❌ Clerk Init: Error testing SDK client: {e}")

    def _convert_to_httpx_request(self, request: Request) -> httpx.Request:
        """Convert FastAPI Request to httpx.Request for Clerk SDK"""
        return httpx.Request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
        )

    def __extract_token_claims_and_authorized_parties(
        self, jwt_token: str
    ) -> dict[str, Any]:
        try:
            import jwt

            decoded_token = jwt.decode(jwt_token, options={"verify_signature": False})
            authorized_party = decoded_token.get("azp", "http://localhost:5173")
            token_claims = decoded_token
        except Exception:
            authorized_party = "http://localhost:5173"
            token_claims = {}
        return token_claims, authorized_party

    def __authenticate_request(
        self, httpx_request: httpx.Request, auth_options
    ) -> dict[str, Any]:
        start_time = time.time()
        try:
            request_state = self.client.authenticate_request(
                httpx_request, auth_options
            )
            end_time = time.time()
            logger.info(
                f"✅ ClerkService: authenticate_request completed in {end_time - start_time:.3f}s"
            )

        except Exception as e:
            raise ClerkAuthenticationError(
                f"Clerk authenticate_request failed: {str(e)}"
            )

        if not request_state.is_signed_in:
            raise ClerkAuthenticationError(
                f"Authentication failed: {getattr(request_state, 'reason', 'Token invalid')}"
            )

        return request_state

    def get_enhanced_auth_data(self, request: Request) -> dict[str, Any]:
        """
        SELF-CONTAINED authentication method that does everything in one place.

        This method performs complete Clerk authentication including:
        1. Token extraction and validation
        2. Clerk authenticate_request call
        3. JWT claims extraction and parsing
        4. User context data extraction
        5. All error handling

        Returns comprehensive auth data for middleware/route use.
        """
        try:
            clerk_secret = os.getenv("CLERK_SECRET_KEY") or settings.CLERK_SECRET_KEY
            if not clerk_secret:
                raise ClerkAuthenticationError("CLERK_SECRET_KEY is required")

            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                raise ClerkAuthenticationError(
                    "Missing or invalid Authorization header"
                )

            token = auth_header[7:]  # Remove "Bearer " prefix
            token_claims, authorized_party = (
                self.__extract_token_claims_and_authorized_parties(token)
            )

            httpx_request = httpx.Request(
                method=request.method,
                url=str(request.url),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            auth_parties = [
                authorized_party,
                "http://localhost:5173",
                "http://localhost:3000",
                "http://localhost:8000",
            ]
            auth_options = AuthenticateRequestOptions(authorized_parties=auth_parties)

            logger.info("🔥 ClerkService: Calling Clerk authenticate_request...")

            request_state = self.__authenticate_request(
                httpx_request=httpx_request, auth_options=auth_options
            )
            clerk_payload = getattr(request_state, "payload", {}) or {}
            user_id = clerk_payload.get("sub")
            session_id = clerk_payload.get("sid")
            org_id = getattr(request_state, "org_id", None)
            org_role = getattr(request_state, "org_role", None)

            jwt_user_id = token_claims.get("sub")
            jwt_session_id = token_claims.get("sid")
            jwt_org_id = token_claims.get("org_id")

            user_role = token_claims.get("role")
            is_app_owner = token_claims.get("isAppOwner", False)

            auth_data = {
                "valid": True,
                "is_signed_in": request_state.is_signed_in,
                "authenticated": True,
                "user_id": user_id or jwt_user_id,
                "clerk_user_id": user_id,
                "session_id": session_id or jwt_session_id,
                "org_id": org_id or jwt_org_id,
                "org_role": org_role,
                "user_role": user_role,
                "is_app_owner": is_app_owner,
                "token": token,
                "token_claims": token_claims,
                "clerk_payload": clerk_payload,
                "all_claims": {**clerk_payload, **token_claims},
                "request_state": request_state,
                "authorized_parties": auth_parties,
                "auth_timestamp": time.time(),
                "token_exp": token_claims.get("exp"),
                "token_iat": token_claims.get("iat"),
            }

            return auth_data

        except ClerkAuthenticationError:
            raise

        except Exception as e:
            raise ClerkAuthenticationError(f"Enhanced authentication failed: {str(e)}")

    def validate_session_token(self, session_token: str) -> dict[str, Any]:
        """
        Validate a Clerk session token and return session information.

        This method validates a raw session token (not from a request)
        and returns the session data if valid.
        """
        try:
            if not session_token:
                raise ClerkAuthenticationError("Session token is required")

            # Extract token claims without signature verification for initial parsing
            token_claims = self.__extract_token_claims_and_authorized_parties(
                session_token
            )[1]

            # Create a mock request for authentication
            import httpx

            mock_request = httpx.Request(
                method="GET",
                url="http://localhost:8000/api/v1/auth/validate",
                headers={
                    "Authorization": f"Bearer {session_token}",
                    "Content-Type": "application/json",
                },
            )

            # Use the same authorized parties as the main auth method
            auth_parties = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://localhost:8000",
            ]
            auth_options = AuthenticateRequestOptions(authorized_parties=auth_parties)

            # Authenticate the request
            request_state = self.__authenticate_request(
                httpx_request=mock_request, auth_options=auth_options
            )

            if not request_state.is_signed_in:
                raise ClerkAuthenticationError("Session token is invalid or expired")

            clerk_payload = getattr(request_state, "payload", {}) or {}
            user_id = clerk_payload.get("sub")
            session_id = clerk_payload.get("sid")

            return {
                "valid": True,
                "user_id": user_id or token_claims.get("sub"),
                "session_id": session_id or token_claims.get("sid"),
                "expires_at": token_claims.get("exp"),
                "issued_at": token_claims.get("iat"),
                "role": token_claims.get("role"),
                "is_app_owner": token_claims.get("isAppOwner", False),
                "org_id": clerk_payload.get("org_id") or token_claims.get("org_id"),
            }

        except ClerkAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Session token validation failed: {str(e)}")
            raise ClerkAuthenticationError(f"Session token validation failed: {str(e)}")
