"""
Enhanced Clerk webhook processor with RBAC integration.

This module extends the existing webhook processor to include:
- Automatic role assignment on user creation
- Updating Clerk metadata with assigned roles
- Role synchronization on user updates
"""

import logging
from typing import Any

from clerk_backend_api import Clerk

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.role_assignment_service import RoleAssignmentService
from app.webhooks.clerk_webhooks import ClerkWebhookProcessor

logger = logging.getLogger(__name__)


class EnhancedClerkWebhookProcessor(ClerkWebhookProcessor):
    """Extended webhook processor with RBAC capabilities."""

    def __init__(self):
        super().__init__()
        self.clerk_client = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)

    async def _process_user_created(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Enhanced user creation processing with role assignment.

        Flow:
        1. Parent method syncs user to database
        2. Get the synced user from database
        3. Use RoleAssignmentService to assign role
        4. Update Clerk user metadata with role name
        """
        clerk_user_id = user_data.get("id")
        if not clerk_user_id:
            logger.error("No clerk user ID found in webhook data")
            return {"success": False, "message": "Invalid webhook data"}

        try:
            sync_result = await super()._process_user_created(user_data)

            with SessionLocal() as session:
                user = self.user_sync_service.find_user_by_clerk_id(
                    session, clerk_user_id
                )
                if not user:
                    logger.error(f"User not found after sync: {clerk_user_id}")
                    return {
                        **sync_result,
                        "role_assignment": {
                            "success": False,
                            "message": "User not found after sync",
                        },
                    }

                role_service = RoleAssignmentService(session)
                role_result = await role_service.assign_initial_role(user, user_data)

                if role_result.get("success"):
                    role_name = role_result.get("role_assigned")
                    is_app_owner = role_name == "app_owner"
                    metadata_result = await self.update_clerk_user_metadata(
                        clerk_user_id, role_name, is_app_owner
                    )
                    role_result["metadata_update"] = metadata_result

                return {**sync_result, "role_assignment": role_result}

        except Exception as e:
            logger.error(f"Error in enhanced user creation processing: {e}")
            return {
                "success": False,
                "message": f"Enhanced processing failed: {str(e)}",
                "clerk_user_id": clerk_user_id,
            }

    async def update_clerk_user_metadata(
        self, clerk_user_id: str, role_name: str, is_app_owner: bool = False
    ) -> dict:
        """
        Update Clerk user's public metadata with role information.

        Args:
            clerk_user_id: Clerk user ID
            role_name: Name of the assigned role
            is_app_owner: Whether user is app owner

        Returns:
            Dictionary with update status
        """
        metadata = {"role": role_name, "isAppOwner": is_app_owner}

        try:
            self.clerk_client.users.update_user_metadata(
                user_id=clerk_user_id, public_metadata=metadata
            )

            logger.info(f"Updated Clerk metadata for user {clerk_user_id}: {metadata}")

            return {
                "success": True,
                "clerk_user_id": clerk_user_id,
                "metadata_updated": metadata,
            }

        except Exception as e:
            logger.error(f"Failed to update Clerk metadata for {clerk_user_id}: {e}")
            return {"success": False, "error": str(e), "clerk_user_id": clerk_user_id}

    async def _process_user_updated(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Enhanced user update processing.

        TODO: Optionally enhance this to handle role changes.
        For example, if user's email domain changes, you might want to re-evaluate their role.
        """

        return await super()._process_user_updated(user_data)
