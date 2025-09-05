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

import httpx
from clerk_backend_api import Clerk, SDKError
from clerk_backend_api.models import (
    CreateJWTTemplateRequestBody,
    CreateOrganizationRequestBody,
    CreateSignInTokenRequestBody,
    GetUserListRequest,
    Organization,
    UpdateOrganizationRequestBody,
    User,
    VerifyOAuthAccessTokenRequestBody,
)
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Request

from app.core.config import settings
from app.core.formatters import AuthOptionsBuilder, ClerkDataFormatter

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

        self.debug = (
            settings.ENVIRONMENT == "local"
            or settings.CLERK_DEBUG
            or os.getenv("CLERK_DEBUG", "").lower() == "true"
        )
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
            clerk_logger = logging.getLogger("clerk_backend_api")
            clerk_logger.setLevel(logging.DEBUG)
            self.logger.info("Clerk debug logging enabled")
        else:
            clerk_logger = logging.getLogger("clerk_backend_api")
            clerk_logger.setLevel(logging.WARNING)

        self.client = Clerk(
            bearer_auth=api_key, debug_logger=clerk_logger if self.debug else None
        )

        self.publishable_key = (
            os.getenv("CLERK_PUBLISHABLE_KEY") or settings.CLERK_PUBLISHABLE_KEY
        )

        self.logger.info(
            f"ClerkService initialized for environment: {settings.ENVIRONMENT}"
        )

    def _convert_to_httpx_request(
        self, request: Request | httpx.Request
    ) -> httpx.Request:
        if hasattr(request, "url") and hasattr(request, "headers"):
            return httpx.Request(
                method=request.method,
                url=str(request.url),
                headers=dict(request.headers),
            )
        return request

    def _get_default_authorized_parties(self) -> list[str]:
        return AuthOptionsBuilder.get_default_authorized_parties(
            settings.FRONTEND_HOST, settings.DOMAIN
        )

    def _create_auth_options(
        self, authorized_parties: list[str] | None, accepts_token: list[str] | None
    ) -> AuthenticateRequestOptions:
        parties = authorized_parties or self._get_default_authorized_parties()
        options = AuthenticateRequestOptions(authorized_parties=parties)
        if accepts_token:
            options.accepts_token = accepts_token
        return options

    def _format_auth_result(
        self, request_state, accepts_token: list[str] | None
    ) -> dict[str, Any]:
        return {
            "valid": True,
            "is_signed_in": request_state.is_signed_in,
            "user_id": getattr(request_state, "user_id", None),
            "session_id": getattr(request_state, "session_id", None),
            "org_id": getattr(request_state, "org_id", None),
            "token_type": "machine" if accepts_token else "session",
        }

    def authenticate_request(
        self,
        request: Request | httpx.Request,
        authorized_parties: list[str] | None = None,
        accepts_token: list[str] | None = None,
    ) -> dict[str, Any]:
        httpx_request = self._convert_to_httpx_request(request)

        try:
            options = self._create_auth_options(authorized_parties, accepts_token)
            request_state = self.client.authenticate_request(httpx_request, options)

            logger.debug(
                f"Authentication result: signed_in={request_state.is_signed_in}"
            )

            if not request_state.is_signed_in:
                raise ClerkAuthenticationError("Request is not authenticated")

            return self._format_auth_result(request_state, accepts_token)

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise ClerkAuthenticationError(f"Authentication failed: {e}")

    def authenticate_session(self, request: Request | httpx.Request) -> dict[str, Any]:
        return self.authenticate_request(request)

    def authenticate_machine_token(
        self, request: Request | httpx.Request
    ) -> dict[str, Any]:
        return self.authenticate_request(request, accepts_token=["oauth_token"])

    def _format_user_data(self, user: User) -> dict[str, Any]:
        return ClerkDataFormatter.format_user_data(user)

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        self.logger.debug(f"Fetching user data for user_id: {user_id}")

        try:
            user: User = self.client.users.get(user_id=user_id)
            if not user:
                return None

            return self._format_user_data(user)

        except SDKError as e:
            if "not found" in str(e).lower():
                return None
            if "unauthorized" in str(e).lower():
                raise ClerkAuthenticationError(f"Clerk API authentication failed: {e}")
            raise ClerkAuthenticationError(f"Failed to get user: {e}")
        except Exception as e:
            raise ClerkAuthenticationError(f"Failed to get user: {e}")

    def list_users(self, email: str | None = None, limit: int = 10) -> dict[str, Any]:
        """List users from Clerk API"""
        self.logger.debug(f"Listing users with email filter: {email}, limit: {limit}")

        try:
            request = GetUserListRequest(
                limit=limit,
                offset=0,
                order_by="-created_at",
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

        # DEBUG: Log webhook signature verification details
        try:
            print("🔍 WEBHOOK SIGNATURE DEBUG STARTING")
            print(f"🔍 Debug enabled: {self.debug}")
            print(
                f"🔍 Webhook secret length: {len(webhook_secret) if webhook_secret else 0}"
            )
            print(
                f"🔍 Webhook secret prefix: {webhook_secret[:10] if webhook_secret else 'None'}..."
            )
            print(f"🔍 All headers: {list(headers.keys())}")
        except Exception as e:
            print(f"🔍 DEBUG ERROR: {e}")

        if self.debug:
            logger.info("=== WEBHOOK SIGNATURE VERIFICATION DEBUG ===")
            logger.info(
                f"Webhook secret length: {len(webhook_secret) if webhook_secret else 0}"
            )
            logger.info(
                f"Webhook secret prefix: {webhook_secret[:10]}..."
                if webhook_secret
                else "None"
            )
            logger.info(f"All headers: {list(headers.keys())}")

        svix_id = headers.get("svix-id")
        svix_timestamp = headers.get("svix-timestamp")
        svix_signature = headers.get("svix-signature")

        print(f"🔍 svix-id: {svix_id}")
        print(f"🔍 svix-timestamp: {svix_timestamp}")
        print(f"🔍 svix-signature: {svix_signature}")

        if self.debug:
            logger.info(f"svix-id: {svix_id}")
            logger.info(f"svix-timestamp: {svix_timestamp}")
            logger.info(f"svix-signature: {svix_signature}")

        if not all([svix_id, svix_timestamp, svix_signature]):
            if self.debug:
                logger.info("❌ Missing required headers")
            return False

        try:
            webhook_time = int(svix_timestamp)
            current_time = time.time()
            time_diff = abs(current_time - webhook_time)
            if self.debug:
                logger.info(
                    f"Webhook time: {webhook_time}, Current time: {current_time}, Diff: {time_diff}s"
                )
            if time_diff > 300:
                if self.debug:
                    logger.info("❌ Webhook timestamp expired (>300s)")
                return False
        except (ValueError, TypeError):
            if self.debug:
                logger.info("❌ Invalid timestamp format")
            return False

        signed_payload = f"{svix_id}.{svix_timestamp}.{payload}"
        if self.debug:
            logger.info(f"Signed payload: {signed_payload[:100]}...")

        secret_key = (
            webhook_secret[6:]
            if webhook_secret.startswith("whsec_")
            else webhook_secret
        )

        if self.debug:
            logger.info(f"Secret key (after prefix removal): {len(secret_key)} chars")

        try:
            secret_bytes = base64.b64decode(secret_key)
            if self.debug:
                logger.info(f"Secret decoded successfully: {len(secret_bytes)} bytes")
        except Exception as e:
            secret_bytes = secret_key.encode("utf-8")
            if self.debug:
                logger.info(f"Secret decode failed, using UTF-8: {e}")

        expected_sig = hmac.new(
            secret_bytes, signed_payload.encode("utf-8"), hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.b64encode(expected_sig).decode("utf-8")

        if self.debug:
            logger.info(f"Expected signature: {expected_sig_b64}")

        sig_string = svix_signature or ""
        provided_signatures = [
            sig[3:] for sig in sig_string.split(" ") if sig.startswith("v1,")
        ]

        if self.debug:
            logger.info(f"Provided signatures count: {len(provided_signatures)}")
            for i, sig in enumerate(provided_signatures):
                logger.info(f"Provided signature {i}: {sig}")
                matches = hmac.compare_digest(expected_sig_b64, sig)
                logger.info(f"Signature {i} matches: {matches}")

        result = any(
            hmac.compare_digest(expected_sig_b64, sig) for sig in provided_signatures
        )

        if self.debug:
            logger.info(
                f"Final verification result: {'✅ VALID' if result else '❌ INVALID'}"
            )
            logger.info("=== END WEBHOOK SIGNATURE DEBUG ===")

        return result

    def _create_organization_request(
        self,
        name: str,
        slug: str | None = None,
        created_by: str | None = None,
        private_metadata: dict[str, Any] | None = None,
        public_metadata: dict[str, Any] | None = None,
    ) -> CreateOrganizationRequestBody:
        return CreateOrganizationRequestBody(
            name=name,
            slug=slug,
            created_by=created_by,
            private_metadata=private_metadata or {},
            public_metadata=public_metadata or {},
        )

    def _format_organization_response(self, response: Organization) -> dict[str, Any]:
        return ClerkDataFormatter.format_organization_full(response)

    def create_organization(
        self,
        name: str,
        slug: str | None = None,
        created_by: str | None = None,
        private_metadata: dict[str, Any] | None = None,
        public_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        logger.info(f"Creating team/organization: {name}")

        try:
            create_request = self._create_organization_request(
                name, slug, created_by, private_metadata, public_metadata
            )

            response = self.client.organizations.create(create_request)

            if not response or not response.id:
                logger.error("Failed to create organization - no response or ID")
                return None

            logger.info(f"Successfully created organization: {response.id}")
            return self._format_organization_response(response)

        except Exception as e:
            logger.error(f"Failed to create organization: {str(e)}")
            raise ClerkAuthenticationError(f"Organization creation failed: {str(e)}")

    def get_organization(self, organization_id: str) -> dict[str, Any] | None:
        logger.debug(f"Fetching organization: {organization_id}")

        try:
            org: Organization = self.client.organizations.get(
                organization_id=organization_id
            )

            if not org:
                return None

            return self._format_organization_response(org)

        except SDKError as e:
            logger.error(
                f"Clerk SDK error fetching organization {organization_id}: {e}"
            )
            if "not found" in str(e).lower():
                return None
            raise ClerkAuthenticationError(f"Failed to get organization: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error fetching organization {organization_id}: {e}"
            )
            raise ClerkAuthenticationError(f"Failed to get organization: {e}")

    def _format_organization_list_item(self, org: Organization) -> dict[str, Any]:
        return ClerkDataFormatter.format_organization_summary(org)

    def list_organizations(
        self, query: str | None = None, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        logger.debug(f"Listing organizations: query={query}, limit={limit}")

        try:
            response = self.client.organizations.list(
                query=query, limit=limit, offset=offset
            )

            organizations = []
            if hasattr(response, "data"):
                for org in response.data:
                    organizations.append(self._format_organization_list_item(org))

            return {
                "organizations": organizations,
                "total_count": getattr(response, "total_count", len(organizations)),
            }

        except Exception as e:
            logger.error(f"Failed to list organizations: {str(e)}")
            raise ClerkAuthenticationError(f"Failed to list organizations: {str(e)}")

    def update_organization(
        self,
        organization_id: str,
        name: str | None = None,
        slug: str | None = None,
        private_metadata: dict[str, Any] | None = None,
        public_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Update organization data.

        Single responsibility: Organization updates only.
        """
        logger.info(f"Updating organization: {organization_id}")

        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if slug is not None:
                update_data["slug"] = slug
            if private_metadata is not None:
                update_data["private_metadata"] = private_metadata
            if public_metadata is not None:
                update_data["public_metadata"] = public_metadata

            if not update_data:
                logger.warning("No update data provided")
                return None

            update_request = UpdateOrganizationRequestBody(**update_data)
            response = self.client.organizations.update(
                organization_id=organization_id, request_body=update_request
            )

            return {
                "id": response.id,
                "name": response.name,
                "slug": response.slug,
                "updated_at": response.updated_at,
                "private_metadata": response.private_metadata or {},
                "public_metadata": response.public_metadata or {},
            }

        except Exception as e:
            logger.error(f"Failed to update organization: {str(e)}")
            raise ClerkAuthenticationError(f"Organization update failed: {str(e)}")

    def delete_organization(self, organization_id: str) -> bool:
        """
        Delete organization.

        Single responsibility: Organization deletion only.
        """
        logger.info(f"Deleting organization: {organization_id}")

        try:
            self.client.organizations.delete(organization_id=organization_id)
            logger.info(f"Successfully deleted organization: {organization_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete organization: {str(e)}")
            raise ClerkAuthenticationError(f"Organization deletion failed: {str(e)}")

    # ===== SIGN-IN TOKEN MANAGEMENT =====
    def create_sign_in_token(
        self, user_id: str, expires_in_seconds: int | None = None
    ) -> dict[str, Any] | None:
        """
        Create sign-in token for programmatic user authentication.

        Critical for MatchBot admin flows:
        - Admin onboarding users
        - Password reset flows
        - Magic link authentication
        - Dating app invite system
        """
        logger.info(f"Creating sign-in token for user: {user_id}")

        try:
            create_request = CreateSignInTokenRequestBody(
                user_id=user_id, expires_in_seconds=expires_in_seconds
            )

            response = self.client.sign_in_tokens.create(create_request)

            return {
                "token": response.token,
                "user_id": response.user_id,
                "status": response.status,
                "url": getattr(response, "url", None),
                "expires_at": getattr(response, "expires_at", None),
            }

        except Exception as e:
            logger.error(f"Failed to create sign-in token: {str(e)}")
            raise ClerkAuthenticationError(f"Sign-in token creation failed: {str(e)}")

    # ===== ENHANCED OAUTH TOKEN VERIFICATION =====
    def verify_oauth_token(self, token: str) -> dict[str, Any] | None:
        """
        Enhanced OAuth access token verification.

        For mobile apps, third-party integrations, service-to-service auth.
        """
        logger.debug("Verifying OAuth access token")

        try:
            verify_request = VerifyOAuthAccessTokenRequestBody(token=token)
            response = self.client.oauth_access_tokens.verify(verify_request)

            return {
                "valid": True,
                "user_id": getattr(response, "user_id", None),
                "client_id": getattr(response, "client_id", None),
                "scopes": getattr(response, "scopes", []),
                "expires_at": getattr(response, "expires_at", None),
            }

        except Exception as e:
            logger.error(f"OAuth token verification failed: {str(e)}")
            raise ClerkAuthenticationError(f"OAuth token verification failed: {str(e)}")

    # ===== JWT TEMPLATES =====
    def create_jwt_template(
        self,
        name: str,
        claims: dict[str, Any],
        lifetime: int | None = None,
        allowed_clock_skew: int | None = None,
    ) -> dict[str, Any] | None:
        """
        Create JWT template with custom claims.

        For MatchBot: Embed dating preferences, premium status, custom roles in tokens.
        """
        logger.info(f"Creating JWT template: {name}")

        try:
            create_request = CreateJWTTemplateRequestBody(
                name=name,
                claims=claims,
                lifetime=lifetime,
                allowed_clock_skew=allowed_clock_skew,
            )

            response = self.client.jwt_templates.create(create_request)

            return {
                "id": response.id,
                "name": response.name,
                "claims": response.claims,
                "lifetime": response.lifetime,
                "created_at": response.created_at,
            }

        except Exception as e:
            logger.error(f"Failed to create JWT template: {str(e)}")
            raise ClerkAuthenticationError(f"JWT template creation failed: {str(e)}")
