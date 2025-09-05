from uuid import uuid4

from fastapi import HTTPException, Request
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User


class TestUsers:
    """Mock users for testing different roles without Clerk API usage"""

    USERS: dict[str, dict] = {
        "regular_user": {
            "id": "test-regular-user-id",
            "email": "test-regular@example.com",
            "full_name": "Test Regular User",
            "clerk_user_id": "clerk_test_regular_123",
        },
        "platform_admin": {
            "id": "test-admin-user-id",
            "email": "test-admin@example.com",
            "full_name": "Test Admin User",
            "clerk_user_id": "clerk_test_admin_123",
        },
        "app_owner": {
            "id": "test-owner-user-id",
            "email": "test-owner@example.com",
            "full_name": "Test Owner User",
            "clerk_user_id": "clerk_test_owner_123",
        },
    }


def get_mock_user_session(request: Request, session: Session) -> User:
    """
    Mock authentication function that replaces Clerk authentication during testing.

    Uses X-Test-Role header to determine which role to authenticate as.
    Valid roles: regular_user, platform_admin, app_owner
    """
    if not settings.ENABLE_AUTH_TESTING:
        raise HTTPException(
            status_code=500, detail="Test authentication is not enabled"
        )

    # Get role from header, default to regular_user
    test_role = request.headers.get("X-Test-Role", "regular_user")

    if test_role not in TestUsers.USERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid test role: {test_role}. Valid roles: {list(TestUsers.USERS.keys())}",
        )

    # Get user data for the requested role
    user_data = TestUsers.USERS[test_role]

    # Find user in database
    statement = select(User).where(User.clerk_user_id == user_data["clerk_user_id"])
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Test user for role '{test_role}' not found in database. Run setup_test_users() first.",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Test user account is inactive")

    return user


async def setup_test_users(session: Session) -> dict[str, str]:
    """
    Create test users in database with proper roles assigned.
    Only runs if ENABLE_AUTH_TESTING is True.
    """
    if not settings.ENABLE_AUTH_TESTING:
        return {"status": "skipped", "reason": "ENABLE_AUTH_TESTING is False"}

    from app.services.rbac_service import RoleService, UserRoleService

    created_users = []
    role_service = RoleService()
    user_role_service = UserRoleService()

    for role_name, user_data in TestUsers.USERS.items():
        # Check if user already exists
        statement = select(User).where(User.clerk_user_id == user_data["clerk_user_id"])
        existing_user = session.exec(statement).first()

        if not existing_user:
            # Create new test user
            user = User(
                id=uuid4(),
                email=user_data["email"],
                full_name=user_data["full_name"],
                clerk_user_id=user_data["clerk_user_id"],
                is_active=True,
                is_superuser=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            created_users.append(f"Created {user_data['email']}")
        else:
            user = existing_user
            created_users.append(f"Found existing {user_data['email']}")

        # Assign role to user
        role = role_service.get_role_by_name(session, role_name)
        if role:
            existing_role = user_role_service.get_user_roles(session, user.id)
            if not any(ur.role_id == role.id for ur in existing_role):
                user_role_service.assign_role_to_user(
                    session=session, user_id=user.id, role_id=role.id
                )
                created_users.append(
                    f"Assigned {role_name} role to {user_data['email']}"
                )
            else:
                created_users.append(
                    f"{user_data['email']} already has {role_name} role"
                )

    return {
        "status": "completed",
        "actions": created_users,
        "instructions": [
            "Set ENABLE_AUTH_TESTING=true in your environment",
            "Use X-Test-Role header in Swagger UI or API calls:",
            "  X-Test-Role: regular_user (for regular user endpoints)",
            "  X-Test-Role: platform_admin (for admin endpoints)",
            "  X-Test-Role: app_owner (for owner-only endpoints)",
        ],
    }
