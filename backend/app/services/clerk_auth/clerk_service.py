"""
Clerk Service

Handles Clerk authentication and user management operations using the actual SDK.
"""

import base64
import hashlib
import hmac
import logging
import os
import time
from typing import Any

from clerk_backend_api import Clerk, SDKError
from clerk_backend_api.models.getuserlistop import GetUserListRequest
from clerk_backend_api.models.session import Session
from clerk_backend_api.models.user import User

from app.core.config import settings

logger = logging.getLogger(__name__)


class ClerkAuthenticationError(Exception):
    """Raised when Clerk authentication operations fail"""

    pass


class ClerkService:
    """Clerk service that handles authentication and user management"""

    def __init__(self) -> None:
        """Initialize Clerk client with logging"""
        api_key = os.getenv("CLERK_SECRET_KEY") or settings.CLERK_SECRET_KEY
        if not api_key:
            raise ClerkAuthenticationError(
                "CLERK_SECRET_KEY is required for production"
            )

        self.logger = logging.getLogger("clerk_service")

        debug_enabled = (
            settings.ENVIRONMENT == "local"
            or settings.CLERK_DEBUG
            or os.getenv("CLERK_DEBUG", "").lower() == "true"
        )
        if debug_enabled:
            logging.basicConfig(level=logging.DEBUG)
            clerk_logger = logging.getLogger("clerk_backend_api")
            clerk_logger.setLevel(logging.DEBUG)
            self.logger.info("Clerk debug logging enabled")
        else:
            clerk_logger = logging.getLogger("clerk_backend_api")
            clerk_logger.setLevel(logging.WARNING)

        self.client = Clerk(
            bearer_auth=api_key, debug_logger=clerk_logger if debug_enabled else None
        )

        self.publishable_key = (
            os.getenv("CLERK_PUBLISHABLE_KEY") or settings.CLERK_PUBLISHABLE_KEY
        )

        self.logger.info(
            f"ClerkService initialized for environment: {settings.ENVIRONMENT}"
        )

    def validate_session_token(self, token: str) -> dict[str, Any]:
        """
        Validate session token by getting session from Clerk API
        """
        if not token or not token.strip():
            raise ClerkAuthenticationError("Session token is required")

        self.logger.debug(f"Validating session token: {token[:10]}...")

        try:
            session: Session = self.client.sessions.get(session_id=token)

            if not session:
                raise ClerkAuthenticationError("Session not found")

            if session.status.value != "active":  # Status is an enum
                self.logger.warning(
                    f"Session validation failed - status: {session.status.value}"
                )
                raise ClerkAuthenticationError(
                    f"Session is not active: {session.status.value}"
                )

            self.logger.debug(
                f"Session validated successfully for user: {session.user_id}"
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
            self.logger.error(f"Clerk SDK error during session validation: {e}")
            if "not found" in str(e).lower():
                raise ClerkAuthenticationError(
                    "Session token has expired or is invalid"
                )
            if "unauthorized" in str(e).lower():
                raise ClerkAuthenticationError(f"Clerk API authentication failed: {e}")
            raise ClerkAuthenticationError(f"Session validation failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during session validation: {e}")
            raise ClerkAuthenticationError(f"Session validation failed: {e}")

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get user data from Clerk API"""
        self.logger.debug(f"Fetching user data for user_id: {user_id}")

        try:
            user: User = self.client.users.get(user_id=user_id)

            if not user:
                self.logger.debug(f"User not found: {user_id}")
                return None

            primary_email = None
            if user.email_addresses:
                for email_obj in user.email_addresses:
                    if email_obj.id == user.primary_email_address_id:
                        primary_email = email_obj.email_address
                        break
                if not primary_email and user.email_addresses:
                    primary_email = user.email_addresses[0].email_address

            self.logger.debug(
                f"Successfully fetched user data for: {user_id} ({primary_email})"
            )

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
            self.logger.error(f"Clerk SDK error fetching user {user_id}: {e}")
            if "not found" in str(e).lower():
                return None
            if "unauthorized" in str(e).lower():
                raise ClerkAuthenticationError(f"Clerk API authentication failed: {e}")
            raise ClerkAuthenticationError(f"Failed to get user: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching user {user_id}: {e}")
            raise ClerkAuthenticationError(f"Failed to get user: {e}")

    def list_users(self, email: str | None = None, limit: int = 10) -> dict[str, Any]:
        """List users from Clerk API"""
        self.logger.debug(f"Listing users with email filter: {email}, limit: {limit}")

        try:
            # Create request object as required by SDK
            request = GetUserListRequest(
                limit=limit,
                offset=0,
                order_by="-created_at",  # Default ordering
            )

            if email:
                request.email_address_query = email

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

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Create a new user in Clerk

        Args:
            email: User's email address
            password: User's password
            first_name: User's first name (optional)
            last_name: User's last name (optional)

        Returns:
            User data dictionary or None if creation failed
        """
        from clerk_backend_api.models.operations import CreateUserRequestBody

        logger.info(f"Creating user with email: {email}")

        try:
            # Prepare user creation request
            create_request = CreateUserRequestBody(
                email_addresses=[email],
                password=password,
                first_name=first_name,
                last_name=last_name,
                skip_password_checks=False,
                skip_password_requirement=False,
            )

            # Create user via Clerk SDK
            response = self.client.users.create(create_request)

            if not response or not response.id:
                logger.error("Failed to create user - no response or ID")
                return None

            # Format response similar to get_user format
            user_data = {
                "id": response.id,
                "email": email,
                "first_name": response.first_name,
                "last_name": response.last_name,
                "has_image": bool(response.image_url),
                "created_at": int(response.created_at / 1000)
                if response.created_at
                else None,
                "updated_at": int(response.updated_at / 1000)
                if response.updated_at
                else None,
            }

            logger.info(f"Successfully created user: {response.id}")
            return user_data

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")

            # Handle specific Clerk errors
            error_message = str(e)
            if "email_address_taken" in error_message.lower():
                raise ClerkAuthenticationError("Email address is already registered")
            elif "password" in error_message.lower():
                raise ClerkAuthenticationError("Password does not meet requirements")
            else:
                raise ClerkAuthenticationError(f"User creation failed: {error_message}")

            return None
