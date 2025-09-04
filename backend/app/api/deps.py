from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.db import engine
from app.models import User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService
from app.services.rbac_service import RoleService, UserRoleService
from app.services.user_sync_service import UserSyncService


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user_session(request: Request, session: SessionDep) -> User:
    """
    Get current user using official Clerk SDK authenticate_request method.

    Single responsibility: Session-based user authentication.
    """
    try:
        clerk_service = ClerkService()
        auth_data = clerk_service.authenticate_session(request)

        clerk_user_id = auth_data.get("user_id")
        if not clerk_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user ID in authenticated request",
            )

        from sqlmodel import select

        statement = select(User).where(User.clerk_user_id == clerk_user_id)
        user = session.exec(statement).first()

        if not user:
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


ClerkSessionUser = Annotated[User, Depends(get_current_user_session)]


def _check_user_permissions(user: User, session: Session, required_permissions: list[str]) -> bool:
    """Helper function to check if user has any of the required permissions."""
    user_role_service = UserRoleService()
    user_roles = user_role_service.get_user_roles(session, user.id)
    
    role_service = RoleService()
    for user_role in user_roles:
        role = role_service.get_role(session, user_role.role_id)
        if role and ("*" in role.permissions or any(perm in role.permissions for perm in required_permissions)):
            return True
    return False


def _check_user_roles(user: User, session: Session, required_roles: list[str]) -> bool:
    """Helper function to check if user has any of the required roles."""
    user_role_service = UserRoleService()
    user_roles = user_role_service.get_user_roles(session, user.id)
    
    role_service = RoleService()
    for user_role in user_roles:
        role = role_service.get_role(session, user_role.role_id)
        if role and role.name in required_roles:
            return True
    return False


def require_permission(permission: str):
    """Create dependency that checks if user has specific permission."""
    def dependency(current_user: ClerkSessionUser, session: SessionDep) -> User:
        if _check_user_permissions(current_user, session, [permission]):
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' required"
        )
    
    return Annotated[User, Depends(dependency)]


def require_role(roles: str | list[str]):
    """Create dependency that checks if user has required role(s)."""
    role_names = [roles] if isinstance(roles, str) else roles
    
    def dependency(current_user: ClerkSessionUser, session: SessionDep) -> User:
        if _check_user_roles(current_user, session, role_names):
            return current_user
        
        role_list = ", ".join(f"'{r}'" for r in role_names)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these roles required: {role_list}"
        )
    
    return Annotated[User, Depends(dependency)]


# Clean type aliases for common role combinations
AppOwnerUser = require_role("app_owner")
AdminUser = require_role(["app_owner", "platform_admin"])
PlatformAdminUser = require_role("platform_admin")

# Backward compatibility aliases
ClerkSessionSuperuser = AdminUser
CurrentUser = ClerkSessionUser  # Add missing CurrentUser alias
