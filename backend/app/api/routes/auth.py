"""
Authentication routes using Clerk
Handles session validation and user authentication
"""

from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.models import Message, User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService
from app.services.user_sync_service import UserSyncError, UserSyncService

router = APIRouter()


class SessionValidationRequest(BaseModel):
    session_token: str


class SessionValidationResponse(BaseModel):
    valid: bool
    user_id: str | None = None
    clerk_user_id: str | None = None
    expires_at: int | None = None
    error: str | None = None


class UserSyncResponse(BaseModel):
    status: str
    user_id: str | None = None
    clerk_user_id: str
    action: str
    message: str | None = None


class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class SignupResponse(BaseModel):
    success: bool
    user_id: str | None = None
    clerk_user_id: str | None = None
    message: str
    errors: list[str] | None = None


class TokenRefreshRequest(BaseModel):
    session_token: str


class TokenRefreshResponse(BaseModel):
    success: bool
    new_token: str | None = None
    expires_at: int | None = None
    message: str
    error: str | None = None


@router.post("/validate-session", response_model=SessionValidationResponse)
async def validate_session(
    request: SessionValidationRequest,
) -> SessionValidationResponse:
    """
    Validate a Clerk session token and return session info
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


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest) -> SignupResponse:
    """
    Create a new user account with Clerk and sync to local database
    """
    try:
        clerk_service = ClerkService()

        # Create user in Clerk
        clerk_user = clerk_service.create_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        if not clerk_user:
            return SignupResponse(
                success=False,
                message="Failed to create user in Clerk",
                errors=["User creation failed"],
            )

        # Sync user to local database
        sync_service = UserSyncService()
        sync_result = await sync_service.fetch_and_sync_user(clerk_user["id"])

        if sync_result and sync_result.get("status") in ["created", "updated"]:
            return SignupResponse(
                success=True,
                user_id=sync_result.get("user_id"),
                clerk_user_id=clerk_user["id"],
                message="User account created successfully",
            )
        else:
            return SignupResponse(
                success=False,
                clerk_user_id=clerk_user["id"],
                message="User created in Clerk but failed to sync to database",
                errors=["Database sync failed"],
            )

    except ClerkAuthenticationError as e:
        return SignupResponse(success=False, message="Signup failed", errors=[str(e)])
    except UserSyncError as e:
        return SignupResponse(
            success=False,
            message="User created but sync failed",
            errors=[f"Sync error: {str(e)}"],
        )
    except Exception as e:
        return SignupResponse(
            success=False, message="Unexpected error during signup", errors=[str(e)]
        )


@router.get("/me", response_model=User)
async def get_current_user(
    authorization: str = Header(None, description="Bearer token from Clerk"),
) -> User:
    """
    Get current user based on Clerk session token
    Automatically syncs user from Clerk if not in local database
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    session_token = authorization.replace("Bearer ", "")

    try:
        clerk_service = ClerkService()
        session_data = clerk_service.validate_session_token(session_token)
        clerk_user_id = session_data.get("user_id")

        if not clerk_user_id:
            raise HTTPException(status_code=401, detail="Invalid session token")

        # Try to get user from local database or sync from Clerk
        sync_service = UserSyncService()
        user_data = await sync_service.fetch_and_sync_user(clerk_user_id)

        if not user_data or user_data.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="User not found")

        # Return the synced user data
        return User(
            id=int(user_data["user_id"]),
            clerk_user_id=user_data["clerk_user_id"],
            email="",  # Will be populated by sync
            is_active=True,
            is_superuser=False,
            full_name="",
        )

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except UserSyncError as e:
        raise HTTPException(status_code=500, detail=f"User sync failed: {str(e)}")


@router.post("/sync-user/{clerk_user_id}", response_model=UserSyncResponse)
async def sync_user_from_clerk(
    clerk_user_id: str,
    authorization: str = Header(None, description="Bearer token from Clerk"),
) -> UserSyncResponse:
    """
    Manually trigger user sync from Clerk
    Requires valid session token for authorization
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    session_token = authorization.replace("Bearer ", "")

    try:
        # Validate the session token first
        clerk_service = ClerkService()
        clerk_service.validate_session_token(session_token)

        # Trigger user sync
        sync_service = UserSyncService()
        result = await sync_service.fetch_and_sync_user(clerk_user_id)

        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="User not found in Clerk")

        return UserSyncResponse(
            status=result["status"],
            user_id=result.get("user_id"),
            clerk_user_id=clerk_user_id,
            action=result.get("action", "sync"),
            message=f"User {result['status']} successfully",
        )

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except UserSyncError as e:
        raise HTTPException(status_code=500, detail=f"User sync failed: {str(e)}")


@router.post("/sync-user-by-email", response_model=UserSyncResponse | Message)
async def sync_user_by_email(
    email: str,
    authorization: str = Header(None, description="Bearer token from Clerk"),
) -> Any:
    """
    Find and sync user by email from Clerk
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    session_token = authorization.replace("Bearer ", "")

    try:
        # Validate the session token first
        clerk_service = ClerkService()
        clerk_service.validate_session_token(session_token)

        # Find and sync user by email
        sync_service = UserSyncService()
        result = await sync_service.sync_user_by_email(email)

        if result is None:
            return Message(message=f"No user found with email: {email}")

        return UserSyncResponse(
            status=result["status"],
            user_id=result.get("user_id"),
            clerk_user_id=result["clerk_user_id"],
            action=result.get("action", "sync"),
            message=f"User {result['status']} successfully",
        )

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except UserSyncError as e:
        raise HTTPException(status_code=500, detail=f"User sync failed: {str(e)}")


@router.get("/sync-stats")
async def get_sync_stats(
    authorization: str = Header(None, description="Bearer token from Clerk"),
) -> dict[str, int]:
    """
    Get synchronization statistics
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    session_token = authorization.replace("Bearer ", "")

    try:
        # Validate the session token first
        clerk_service = ClerkService()
        clerk_service.validate_session_token(session_token)

        # Get sync stats
        sync_service = UserSyncService()
        return sync_service.get_sync_stats()

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except UserSyncError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync stats: {str(e)}"
        )


@router.post("/refresh-token", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest) -> TokenRefreshResponse:
    """
    Refresh a Clerk session token if it's close to expiring

    Note: Clerk handles session management internally. This endpoint validates
    the current session and returns information about its validity.
    Actual token refresh is handled by Clerk's frontend SDK.
    """
    try:
        clerk_service = ClerkService()
        session_data = clerk_service.validate_session_token(request.session_token)

        if not session_data.get("valid"):
            return TokenRefreshResponse(
                success=False,
                message="Session token is invalid or expired",
                error="Invalid session token",
            )

        # Check if session is close to expiring (within 10 minutes)
        expires_at = session_data.get("expire_at")
        if expires_at:
            import time

            current_time = int(time.time())
            time_until_expiry = expires_at - current_time

            if time_until_expiry < 600:  # Less than 10 minutes
                return TokenRefreshResponse(
                    success=False,
                    message="Session is close to expiring. Please re-authenticate with Clerk.",
                    error="Session expiring soon",
                    expires_at=expires_at,
                )

        # Session is still valid
        return TokenRefreshResponse(
            success=True,
            new_token=request.session_token,  # Clerk manages actual tokens
            expires_at=expires_at,
            message="Session is still valid",
        )

    except ClerkAuthenticationError as e:
        return TokenRefreshResponse(
            success=False, message="Failed to validate session", error=str(e)
        )
    except Exception as e:
        return TokenRefreshResponse(
            success=False, message="Unexpected error during token refresh", error=str(e)
        )
