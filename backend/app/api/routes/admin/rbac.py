from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_db, require_role
from app.models.user import User
from app.services.rbac_service import RoleService, UserRoleService
from app.webhooks.enhanced_clerk_webhooks import EnhancedClerkWebhookProcessor

router = APIRouter()


class UserRoleAssignRequest(BaseModel):
    user_id: UUID
    role_name: str


class UserRoleResponse(BaseModel):
    success: bool
    message: str
    user_id: UUID
    role_name: str | None = None
    user_role_id: UUID | None = None


class UserRolesListResponse(BaseModel):
    user_id: UUID
    roles: list[dict[str, Any]]


@router.post("/users/assign-role", response_model=UserRoleResponse)
async def assign_role_to_user(
    request: UserRoleAssignRequest,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role("app_owner"))],
) -> UserRoleResponse:
    """
    Assign a role to a user. Only app owners can assign roles.

    Args:
        request: User ID and role name to assign
        session: Database session
        _: App owner authentication dependency

    Returns:
        Role assignment result
    """
    try:
        user = session.get(User, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        role_service = RoleService()
        role = role_service.get_role_by_name(session, request.role_name)
        if not role:
            raise HTTPException(
                status_code=404, detail=f"Role '{request.role_name}' not found"
            )

        user_role_service = UserRoleService()

        existing_role = user_role_service.get_user_roles(session, request.user_id)
        if any(ur.role_id == role.id for ur in existing_role):
            return UserRoleResponse(
                success=False,
                message=f"User already has role '{request.role_name}'",
                user_id=request.user_id,
                role_name=request.role_name,
            )

        user_role = user_role_service.assign_role_to_user(
            session=session, user_id=request.user_id, role_id=role.id
        )

        if user.clerk_user_id:
            try:
                webhook_processor = EnhancedClerkWebhookProcessor()
                is_app_owner = request.role_name == "app_owner"
                await webhook_processor.update_clerk_user_metadata(
                    user.clerk_user_id, request.role_name, is_app_owner
                )
            except Exception:
                pass

        return UserRoleResponse(
            success=True,
            message=f"Successfully assigned role '{request.role_name}' to user",
            user_id=request.user_id,
            role_name=request.role_name,
            user_role_id=user_role.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign role: {str(e)}")


@router.delete("/users/{user_id}/roles/{role_name}")
async def remove_role_from_user(
    user_id: UUID,
    role_name: str,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role("app_owner"))],
) -> UserRoleResponse:
    """
    Remove a role from a user. Only app owners can remove roles.

    Args:
        user_id: User ID to remove role from
        role_name: Role name to remove
        session: Database session
        _: App owner authentication dependency

    Returns:
        Role removal result
    """
    try:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        role_service = RoleService()
        role = role_service.get_role_by_name(session, role_name)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")

        user_role_service = UserRoleService()
        success = user_role_service.remove_role_from_user(
            session=session, user_id=user_id, role_id=role.id
        )

        if not success:
            return UserRoleResponse(
                success=False,
                message=f"User does not have role '{role_name}'",
                user_id=user_id,
                role_name=role_name,
            )

        if user.clerk_user_id:
            try:
                remaining_roles = user_role_service.get_user_roles(session, user_id)
                if remaining_roles:
                    remaining_role = role_service.get_role(
                        session, remaining_roles[0].role_id
                    )
                    new_role_name = (
                        remaining_role.name if remaining_role else "regular_user"
                    )
                else:
                    new_role_name = "regular_user"

                webhook_processor = EnhancedClerkWebhookProcessor()
                is_app_owner = new_role_name == "app_owner"
                await webhook_processor.update_clerk_user_metadata(
                    user.clerk_user_id, new_role_name, is_app_owner
                )
            except Exception:
                pass

        return UserRoleResponse(
            success=True,
            message=f"Successfully removed role '{role_name}' from user",
            user_id=user_id,
            role_name=role_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove role: {str(e)}")


@router.get("/users/{user_id}/roles", response_model=UserRolesListResponse)
async def get_user_roles(
    user_id: UUID,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> UserRolesListResponse:
    """
    Get all roles assigned to a user.

    Args:
        user_id: User ID to get roles for
        session: Database session
        _: Admin authentication dependency

    Returns:
        User's assigned roles
    """
    try:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_role_service = UserRoleService()
        user_roles = user_role_service.get_user_roles(session, user_id)

        role_service = RoleService()
        roles = []
        for user_role in user_roles:
            role = role_service.get_role(session, user_role.role_id)
            if role:
                roles.append(
                    {
                        "id": str(role.id),
                        "name": role.name,
                        "permissions": role.permissions,
                        "assigned_at": user_role.assigned_at.isoformat()
                        if user_role.assigned_at
                        else None,
                    }
                )

        return UserRolesListResponse(user_id=user_id, roles=roles)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user roles: {str(e)}"
        )
