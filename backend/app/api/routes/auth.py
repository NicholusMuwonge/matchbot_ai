"""
Authentication routes using Clerk
Handles session validation and current user retrieval only

## Correct Clerk Authentication Flow:
1. **Frontend → Clerk**: User signs up/logs in directly with Clerk
   - Handles email verification, social auth, 2FA, password requirements
   - Returns session tokens to frontend

2. **Clerk → Backend**: Webhook notifications for user lifecycle events
   - `user.created` → Creates user in local database
   - `user.updated` → Updates user in local database
   - `user.deleted` → Removes user from local database

3. **Frontend → Backend**: API requests with Clerk session tokens
   - `/validate-session` → Validates tokens
   - `/me` → Gets current user info

4. **Admin Operations**: User sync operations (see `/users/clerk/*` endpoints)

## Single Responsibility Per Endpoint:
- `/validate-session`: Token validation only
- `/me`: Current user retrieval only (auth handled by dependency)
"""

from fastapi import APIRouter, Security
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from app.api.deps import ClerkSessionUser
from app.models import User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService

router = APIRouter()

# Security scheme for Swagger UI
security = HTTPBearer()


class SessionValidationRequest(BaseModel):
    session_token: str


class SessionValidationResponse(BaseModel):
    valid: bool
    user_id: str | None = None
    clerk_user_id: str | None = None
    expires_at: int | None = None
    error: str | None = None


@router.post("/validate-session", response_model=SessionValidationResponse)
async def validate_session(
    request: SessionValidationRequest,
) -> SessionValidationResponse:
    """
    Validate a Clerk session token and return session info.

    Single responsibility: Session token validation only.
    """
    try:
        clerk_service = ClerkService()
        session_data = clerk_service.validate_session_token(request.session_token)

        return SessionValidationResponse(
            valid=True,
            user_id=session_data.get("user_id"),
            clerk_user_id=session_data.get("user_id"),
            expires_at=session_data.get("expires_at"),
        )

    except ClerkAuthenticationError as e:
        return SessionValidationResponse(valid=False, error=str(e))


# Signup is handled by Clerk frontend + webhooks flow:
# 1. Frontend uses Clerk for signup (handles email verification, social auth, etc.)
# 2. Clerk sends user.created webhook to backend
# 3. Webhook handler syncs user to local database
# See: /webhooks/clerk for webhook handling


@router.get("/me", response_model=User, dependencies=[Security(security)])
async def get_current_user(current_user: ClerkSessionUser) -> User:
    """
    Get the current authenticated user using session token.

    Single responsibility: Return current user info only.
    Authentication and user sync handled by ClerkSessionUser dependency.

    **Authentication Required**: Use Bearer token in Authorization header.
    Get your token from: /api/v1/swagger-auth/get-token-from-browser
    """
    return current_user
