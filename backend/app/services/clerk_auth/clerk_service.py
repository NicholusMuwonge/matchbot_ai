"""
Clerk Service

Handles Clerk authentication and user management operations using the actual SDK.
"""

import base64
import hashlib
import hmac
import os
import time
from typing import Any

from clerk_backend_api import Clerk, SDKError
from clerk_backend_api.models.getuserlistop import GetUserListRequest
from clerk_backend_api.models.session import Session
from clerk_backend_api.models.user import User

from app.core.config import settings


class ClerkAuthenticationError(Exception):
    """Raised when Clerk authentication operations fail"""

    pass


class ClerkService:
    """Clerk service that handles authentication and user management"""

    def __init__(self) -> None:
        """Initialize Clerk client"""
        api_key = os.getenv("CLERK_SECRET_KEY") or settings.CLERK_SECRET_KEY
        if not api_key:
            raise ClerkAuthenticationError(
                "CLERK_SECRET_KEY is required for production"
            )

        self.client = Clerk(bearer_auth=api_key)
        self.publishable_key = (
            os.getenv("CLERK_PUBLISHABLE_KEY") or settings.CLERK_PUBLISHABLE_KEY
        )

    async def validate_session_token(self, token: str) -> dict[str, Any]:
        """
        Validate session token by getting session from Clerk API
        """
        if not token or not token.strip():
            raise ClerkAuthenticationError("Session token is required")

        try:
            session: Session = self.client.sessions.get(session_id=token)

            if not session:
                raise ClerkAuthenticationError("Session not found")

            if session.status.value != "active":  # Status is an enum
                raise ClerkAuthenticationError(
                    f"Session is not active: {session.status.value}"
                )

            return {
                "valid": True,
                "session_id": session.id,
                "user_id": session.user_id,
                "status": session.status.value,
                "expire_at": session.expire_at,  # This is int timestamp
                "created_at": session.created_at,  # This is int timestamp
            }

        except SDKError as e:
            if "not found" in str(e).lower():
                raise ClerkAuthenticationError(
                    "Session token has expired or is invalid"
                )
            if "unauthorized" in str(e).lower():
                raise ClerkAuthenticationError(f"Clerk API authentication failed: {e}")
            raise ClerkAuthenticationError(f"Session validation failed: {e}")
        except Exception as e:
            raise ClerkAuthenticationError(f"Session validation failed: {e}")

    async def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get user data from Clerk API"""
        try:
            # Use users.get() with user_id - this is the actual method
            user: User = self.client.users.get(user_id=user_id)

            if not user:
                return None

            # Extract primary email from email_addresses list (actual SDK structure)
            primary_email = None
            if user.email_addresses:
                for email_obj in user.email_addresses:
                    if email_obj.id == user.primary_email_address_id:
                        primary_email = email_obj.email_address
                        break
                # Fallback to first email if no primary found
                if not primary_email and user.email_addresses:
                    primary_email = user.email_addresses[0].email_address

            return {
                "id": user.id,
                "email": primary_email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "image_url": getattr(user, "image_url", None),  # Check if exists
                "has_image": user.has_image,
                "created_at": getattr(user, "created_at", None),  # May not exist
                "updated_at": getattr(user, "updated_at", None),  # May not exist
            }

        except SDKError as e:
            if "not found" in str(e).lower():
                return None
            if "unauthorized" in str(e).lower():
                raise ClerkAuthenticationError(f"Clerk API authentication failed: {e}")
            raise ClerkAuthenticationError(f"Failed to get user: {e}")
        except Exception as e:
            raise ClerkAuthenticationError(f"Failed to get user: {e}")

    async def list_users(
        self, email: str | None = None, limit: int = 10
    ) -> dict[str, Any]:
        """List users from Clerk API"""
        try:
            # Create request object as required by SDK
            request = GetUserListRequest(
                limit=limit,
                offset=0,
                order_by="-created_at",  # Default ordering
            )

            # Add email filter if provided
            if email:
                request.email_address_query = email

            # Use users.list() with request object - this is the actual method
            users_list: list[User] = self.client.users.list(request=request)

            if not users_list:
                return {"data": [], "total_count": 0}

            users = []
            for user in users_list:
                primary_email = None
                if user.email_addresses:
                    for email_obj in user.email_addresses:
                        if email_obj.id == user.primary_email_address_id:
                            primary_email = email_obj.email_address
                            break
                    # Fallback to first email if no primary found
                    if not primary_email and user.email_addresses:
                        primary_email = user.email_addresses[0].email_address

                users.append(
                    {
                        "id": user.id,
                        "email": primary_email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "image_url": getattr(user, "image_url", None),
                        "has_image": user.has_image,
                        "created_at": getattr(user, "created_at", None),
                    }
                )

            return {
                "data": users,
                "total_count": len(users),  # SDK doesn't return total_count in list
            }

        except SDKError as e:
            if "unauthorized" in str(e).lower():
                raise ClerkAuthenticationError(f"Clerk API authentication failed: {e}")
            raise ClerkAuthenticationError(f"Failed to list users: {e}")
        except Exception as e:
            raise ClerkAuthenticationError(f"Failed to list users: {e}")

    def verify_webhook_signature(self, payload: str, headers: dict[str, str]) -> bool:
        """
        Verify Clerk webhook signature using SVIX format
        """
        webhook_secret = (
            os.getenv("CLERK_WEBHOOK_SECRET") or settings.CLERK_WEBHOOK_SECRET
        )
        if not webhook_secret:
            raise ClerkAuthenticationError(
                "CLERK_WEBHOOK_SECRET is required for production"
            )

        svix_id = headers.get("svix-id")
        svix_timestamp = headers.get("svix-timestamp")
        svix_signature = headers.get("svix-signature")

        if not all([svix_id, svix_timestamp, svix_signature]):
            return False

        # Check timestamp (must be within 5 minutes)
        try:
            webhook_time = int(svix_timestamp)
            if abs(time.time() - webhook_time) > 300:  # 5 minutes
                return False
        except (ValueError, TypeError):
            return False

        signed_payload = f"{svix_id}.{svix_timestamp}.{payload}"

        # Get secret key (remove whsec_ prefix if present)
        secret_key = (
            webhook_secret[6:]
            if webhook_secret.startswith("whsec_")
            else webhook_secret
        )

        try:
            secret_bytes = base64.b64decode(secret_key)
        except Exception:
            # If not base64, use as-is
            secret_bytes = secret_key.encode("utf-8")

        expected_sig = hmac.new(
            secret_bytes, signed_payload.encode("utf-8"), hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.b64encode(expected_sig).decode("utf-8")

        # Check against provided signatures (format: "v1,signature")
        sig_string = svix_signature or ""
        provided_signatures = [
            sig[3:] for sig in sig_string.split(" ") if sig.startswith("v1,")
        ]

        return any(
            hmac.compare_digest(expected_sig_b64, sig) for sig in provided_signatures
        )
