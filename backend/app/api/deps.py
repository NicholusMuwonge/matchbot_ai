from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.db import engine
from app.models import User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService
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

def require_permission(permission: str):
    """
    Decorator that checks if current user has specific permission.
    
    Args:
        permission: Permission string (e.g., "users:write", "admin:read")
        
    Usage:
        @require_permission("users:write")
        def create_user(current_user: ClerkSessionUser):
            pass
    """
    def dependency(current_user: ClerkSessionUser, session: SessionDep) -> User:
        from app.services.rbac_service import RoleService, UserRoleService
        
        user_role_service = UserRoleService()
        user_roles = user_role_service.get_user_roles(session, current_user.id)
        
        role_service = RoleService()
        for user_role in user_roles:
            role = role_service.get_role(session, user_role.role_id)
            if role and (permission in role.permissions or "*" in role.permissions):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' required"
        )
    
    return Annotated[User, Depends(dependency)]


def require_role(roles: str | list[str]):
    """
    Factory function that creates a dependency for role-based authorization.
    
    Args:
        roles: Role name or list of role names (e.g., "app_owner" or ["app_owner", "platform_admin"])
        
    Returns:
        Annotated dependency that checks user roles
        
    Usage:
        AdminUser = require_role(["app_owner", "platform_admin"])
        
        def some_endpoint(current_user: AdminUser):
            pass
    """
    # Normalize to list for consistent handling
    role_names = [roles] if isinstance(roles, str) else roles
    
    def dependency(current_user: ClerkSessionUser, session: SessionDep) -> User:
        from app.services.rbac_service import RoleService, UserRoleService
        
        user_role_service = UserRoleService()
        user_roles = user_role_service.get_user_roles(session, current_user.id)
        
        role_service = RoleService()
        for user_role in user_roles:
            role = role_service.get_role(session, user_role.role_id)
            if role and role.name in role_names:
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

# Backward compatibility alias
ClerkSessionSuperuser = AdminUser
