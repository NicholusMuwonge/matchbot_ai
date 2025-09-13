"""
Shared formatters and utilities for consistent data formatting across the application.

This module provides reusable formatting functions following Python's approach
to shared functionality (similar to Ruby's concerns/mixins).
"""

from typing import Any

from clerk_backend_api.models import Organization, User


class ClerkDataFormatter:
    """Shared formatter for Clerk API data objects."""

    @staticmethod
    def format_user_data(user: User) -> dict[str, Any]:
        """Format Clerk User object into consistent dictionary format."""
        primary_email = ClerkDataFormatter._extract_primary_email(user)

        return {
            "id": user.id,
            "email": primary_email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "image_url": getattr(user, "image_url", None),
            "has_image": user.has_image,
            "created_at": getattr(user, "created_at", None),
            "updated_at": getattr(user, "updated_at", None),
        }

    @staticmethod
    def format_organization_full(org: Organization) -> dict[str, Any]:
        """Format Organization object with full details."""
        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "created_by": org.created_by,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
            "members_count": getattr(org, "members_count", 0),
            "private_metadata": org.private_metadata or {},
            "public_metadata": org.public_metadata or {},
        }

    @staticmethod
    def format_organization_summary(org: Organization) -> dict[str, Any]:
        """Format Organization object for list views (summary data only)."""
        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "members_count": getattr(org, "members_count", 0),
            "public_metadata": org.public_metadata or {},
        }

    @staticmethod
    def _extract_primary_email(user: User) -> str | None:
        """Extract primary email address from user object."""
        if not user.email_addresses:
            return None

        for email_obj in user.email_addresses:
            if email_obj.id == user.primary_email_address_id:
                return email_obj.email_address
        return user.email_addresses[0].email_address


class TeamResponseFormatter:
    """Shared formatter for team/organization response objects."""

    @staticmethod
    def format_team_metadata(
        team_type: str, description: str | None = None, max_users: int | None = None
    ) -> dict[str, Any]:
        """Format team metadata for organization creation."""
        return {
            "team_type": team_type,
            "description": description,
            "max_users": max_users,
        }

    @staticmethod
    def format_full_team_response(org_data: dict[str, Any]) -> dict[str, Any]:
        """Format complete team response from organization data."""
        return {
            "id": org_data["id"],
            "name": org_data["name"],
            "team_type": org_data["public_metadata"].get("team_type", "corporate"),
            "created_by": org_data["created_by"],
            "created_at": org_data["created_at"],
            "members_count": org_data["members_count"],
            "description": org_data["public_metadata"].get("description"),
            "max_users": org_data["public_metadata"].get("max_users"),
        }

    @staticmethod
    def format_list_team_response(
        org_data: dict[str, Any], team_type: str
    ) -> dict[str, Any]:
        """Format team response for list views (privacy-filtered)."""
        return {
            "id": org_data["id"],
            "name": org_data["name"],
            "team_type": team_type,
            "created_by": None,  # Privacy filtered
            "created_at": None,  # Privacy filtered
            "members_count": org_data["members_count"],
            "description": org_data["public_metadata"].get("description"),
            "max_users": org_data["public_metadata"].get("max_users"),
        }
