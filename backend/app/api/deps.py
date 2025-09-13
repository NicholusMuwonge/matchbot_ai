import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.db import engine
from app.models import User
from app.services.user_sync_service import UserSyncService

# Configure logger for detailed error tracking
logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user_session(request: Request, session: SessionDep) -> User:
    """
    Get current user from middleware authentication.

    This function now simply reads authentication data from request.state
    that was set by AuthMiddleware, instead of doing authentication itself.
    """
    logger.info("🔥 get_current_user_session: Reading auth data from middleware")

    # Check if middleware ran and set auth data
    if not hasattr(request.state, "authenticated"):
        logger.error(
            "❌ AuthMiddleware did not run - request.state.authenticated missing"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication middleware not configured",
        )

    # Check if authentication was successful
    if not request.state.authenticated:
        auth_error = getattr(request.state, "auth_error", "Authentication failed")
        logger.error(f"❌ Authentication failed in middleware: {auth_error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_error,
        )

    # Get auth data from middleware
    auth_data = request.state.auth_data
    clerk_user_id = auth_data.get("user_id")

    if not clerk_user_id:
        logger.error("❌ No user ID in middleware auth data")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user ID in authenticated request",
        )

    # Get user from database
    from sqlmodel import select

    statement = select(User).where(User.clerk_user_id == clerk_user_id)
    user = session.exec(statement).first()

    if not user:
        logger.info("🔍 User not found, attempting sync from Clerk")
        sync_service = UserSyncService()
        sync_result = sync_service.fetch_and_sync_user(clerk_user_id)

        if sync_result and sync_result.get("user_id"):
            user = session.get(User, sync_result["user_id"])

    if not user:
        logger.error("❌ User not found in database after sync attempt")
        raise HTTPException(status_code=404, detail="User not found in database")

    if not user.is_active:
        logger.error("❌ User account is inactive")
        raise HTTPException(status_code=400, detail="User account is inactive")

    user._auth_data = auth_data
    user._auth_claims = auth_data.get("all_claims", {})

    logger.info(f"✅ Got authenticated user from middleware: {user.email}")
    return user


ClerkSessionUser = Annotated[User, Depends(get_current_user_session)]


CurrentUser = ClerkSessionUser
