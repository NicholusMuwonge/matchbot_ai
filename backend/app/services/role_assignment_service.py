"""
Role Assignment Service for automatic role assignment based on business rules.

This service determines which role(s) a user should have based on:
- Email domain
- Organization membership
- Manual overrides
- Default roles
"""

import logging
import os

from sqlmodel import Session

from app.models.rbac import Role
from app.models.user import User
from app.services.rbac_service import RoleService, UserRoleService

logger = logging.getLogger(__name__)


class RoleAssignmentException(Exception):
    pass


class RoleAssignmentService:
    """Service for determining and assigning roles to users."""

    def __init__(self, session: Session):
        self.session = session
        self.role_service = RoleService()
        self.user_role_service = UserRoleService()

    def determine_user_role(self, user_data: dict) -> Role | None:
        """
        Determine which role a user should have based on business rules.

        Args:
            user_data: Clerk user data dictionary containing:
                - id: Clerk user ID
                - email_addresses: List of email objects
                - first_name, last_name: User's name

        Returns:
            Role object or None if no role found
        """
        primary_email = self.get_primary_email(user_data)
        if not primary_email:
            logger.warning(f"No verified email found for user {user_data.get('id')}")
            return None

        logger.info(f"Determining role for email: {primary_email}")

        if primary_email.endswith("@matchbot.ai"):
            return self.role_service.get_role_by_name(self.session, "platform_admin")

        app_owner_email = os.getenv("APP_OWNER_EMAIL")
        if app_owner_email and primary_email.lower() == app_owner_email.lower():
            return self.role_service.get_role_by_name(self.session, "app_owner")

        return self.role_service.get_role_by_name(self.session, "regular_user")

    async def assign_initial_role(self, user: User, user_data: dict) -> dict:
        """
        Assign initial role to a newly created user.

        Args:
            user: The User model instance
            user_data: Clerk user data

        Returns:
            Dictionary with assignment results
        """
        try:
            role = self.determine_user_role(user_data)
            if not role:
                return {
                    "success": False,
                    "message": "No appropriate role found for user",
                    "user_id": user.id,
                }

            user_role = self.user_role_service.assign_role_to_user(
                session=self.session, user_id=user.id, role_id=role.id
            )

            logger.info(
                f"Assigned {role.name} role to user {user.email or user.clerk_user_id}"
            )

            return {
                "success": True,
                "role_assigned": role.name,
                "user_id": user.id,
                "user_role_id": user_role.id,
                "message": f"Successfully assigned {role.name} role to user",
            }

        except Exception as e:
            logger.error(f"Failed to assign role to user {user.id}: {e}")
            return {
                "success": False,
                "message": f"Role assignment failed: {str(e)}",
                "user_id": user.id,
            }

    def get_primary_email(self, user_data: dict) -> str | None:
        """
        Extract primary verified email from Clerk user data.

        Args:
            user_data: Clerk user data with email_addresses list

        Returns:
            Primary verified email address or None
        """
        emails = user_data.get("email_addresses", [])
        if not emails:
            return None

        for email in emails:
            verification = email.get("verification", {})
            is_verified = verification.get("status") == "verified"
            is_primary = email.get("primary", False)

            if is_primary and is_verified:
                return email.get("email_address")

        for email in emails:
            verification = email.get("verification", {})
            is_verified = verification.get("status") == "verified"

            if is_verified:
                return email.get("email_address")

        return None
