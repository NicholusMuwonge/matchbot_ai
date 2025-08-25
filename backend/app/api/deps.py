from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService
from app.services.user_sync_service import UserSyncService

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


# Clerk Authentication Dependencies
clerk_bearer = HTTPBearer()

ClerkTokenDep = Annotated[str, Depends(clerk_bearer)]


def get_clerk_current_user(
    session: SessionDep, credentials: Annotated[HTTPBearer, Depends(clerk_bearer)]
) -> User:
    """
    Get current user using Clerk session token validation
    """
    try:
        token = credentials.credentials

        # Validate session with Clerk
        clerk_service = ClerkService()
        session_data = clerk_service.validate_session_token(token)

        if not session_data.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token",
            )

        clerk_user_id = session_data.get("user_id")
        if not clerk_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session - no user ID",
            )

        # Get or sync user from database
        from sqlmodel import select

        statement = select(User).where(User.clerk_user_id == clerk_user_id)
        user = session.exec(statement).first()

        if not user:
            # Try to sync user from Clerk
            sync_service = UserSyncService()
            sync_result = sync_service.fetch_and_sync_user(clerk_user_id)

            if sync_result and sync_result.get("user_id"):
                user = session.get(User, sync_result["user_id"])

        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        if not user.is_active:
            raise HTTPException(status_code=400, detail="User account is inactive")

        return user

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


ClerkCurrentUser = Annotated[User, Depends(get_clerk_current_user)]


def get_clerk_current_active_superuser(current_user: ClerkCurrentUser) -> User:
    """
    Dependency to ensure current user has superuser privileges (Clerk-based)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


ClerkCurrentSuperuser = Annotated[User, Depends(get_clerk_current_active_superuser)]
