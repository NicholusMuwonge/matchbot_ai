import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session

from app.core.db import engine
from app.models import (
    WebhookEvent,
    WebhookStateMachine,
    WebhookStatus,
    WebhookTransitionError,
)
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService
from app.services.user_sync_service import UserSyncError, UserSyncService

# from app.tasks.user_sync_tasks import (
#     schedule_user_delete,
#     schedule_user_sync,
# )

logger = logging.getLogger(__name__)


class WebhookProcessingError(Exception):
    pass


async def process_clerk_webhook(
    webhook_data: dict[str, Any],
    headers: dict[str, str],
    session: Session = None,
    raw_body: str = None,
) -> dict[str, Any]:
    processor = ClerkWebhookProcessor()
    return await processor.process_webhook_with_verification(
        webhook_data, headers, session, raw_body
    )


class ClerkWebhookProcessor:
    def __init__(self):
        self.clerk_service = ClerkService()
        self.user_sync_service = UserSyncService()

    async def process_webhook_with_verification(
        self,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
        session: Session = None,
        raw_body: str = None,
    ) -> dict[str, Any]:
        webhook_id = headers.get(
            "svix-id", f"webhook_{datetime.now(timezone.utc).isoformat()}"
        )
        # Use raw body for signature verification, fallback to re-serialized JSON
        payload_str = raw_body if raw_body else json.dumps(webhook_data, sort_keys=True)

        if session is None:
            with Session(engine) as session:
                return await self._process_with_session(
                    webhook_data, headers, payload_str, webhook_id, session
                )
        else:
            return await self._process_with_session(
                webhook_data, headers, payload_str, webhook_id, session
            )

    async def _process_with_session(
        self,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
        payload_str: str,
        webhook_id: str,
        session: Session,
    ) -> dict[str, Any]:
        """Process webhook within a database session"""
        existing_webhook = self._get_webhook_by_id(session, webhook_id)
        if existing_webhook and existing_webhook.status == WebhookStatus.SUCCESS:
            return {
                "status": "already_processed",
                "webhook_id": webhook_id,
                "message": "Webhook already processed successfully",
            }
        webhook_event = existing_webhook or self._create_webhook_event(
            session, webhook_id, webhook_data, headers
        )

        try:
            is_valid = self.clerk_service.verify_webhook_signature(payload_str, headers)

            if not is_valid:
                webhook_event.status = WebhookStatus.INVALID
                webhook_event.error_message = "Invalid webhook signature"
                session.commit()

                return {
                    "status": "invalid",
                    "webhook_id": webhook_id,
                    "error": "Invalid webhook signature",
                }
            webhook_event.status = WebhookStatus.PROCESSING
            session.commit()

            result = await self.process_webhook(webhook_data)
            webhook_event.status = WebhookStatus.SUCCESS
            webhook_event.processed_at = datetime.now(timezone.utc)
            webhook_event.processed_data = result
            session.commit()

            return {
                **result,
                "webhook_id": webhook_id,
                "processed_at": webhook_event.processed_at.isoformat(),
            }

        except Exception as e:
            webhook_event.status = WebhookStatus.FAILED
            webhook_event.error_message = str(e)
            webhook_event.retry_count += 1
            retry_delay_minutes = min(2**webhook_event.retry_count, 60)
            webhook_event.next_retry_at = datetime.now(timezone.utc) + timedelta(
                minutes=retry_delay_minutes
            )

            session.commit()

            return {
                "status": "failed",
                "webhook_id": webhook_id,
                "error": str(e),
                "retry_count": webhook_event.retry_count,
                "next_retry_at": webhook_event.next_retry_at.isoformat()
                if webhook_event.next_retry_at
                else None,
            }

    async def process_webhook(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """Process webhook based on event type - core business logic"""
        event_type = webhook_data.get("type")
        event_data = webhook_data.get("data", {})

        try:
            if event_type == "user.created":
                return await self._process_user_created(event_data)
            elif event_type == "user.updated":
                return await self._process_user_updated(event_data)
            elif event_type == "user.deleted":
                return await self._process_user_deleted(event_data)

            # Organization events (for MatchBot B2B teams)
            elif event_type == "organization.created":
                return await self._process_organization_created(event_data)
            elif event_type == "organization.updated":
                return await self._process_organization_updated(event_data)
            elif event_type == "organization.deleted":
                return await self._process_organization_deleted(event_data)
            elif event_type == "organizationMembership.created":
                return await self._process_organization_membership_created(event_data)
            elif event_type == "organizationMembership.deleted":
                return await self._process_organization_membership_deleted(event_data)
            elif event_type == "organizationMembership.updated":
                return await self._process_organization_membership_updated(event_data)

            # Session events
            elif event_type == "session.created":
                return await self._process_session_created(event_data)
            elif event_type == "session.ended":
                return await self._process_session_ended(event_data)

            # Email/SMS events
            elif event_type == "email.created":
                return await self._process_email_created(event_data)
            elif event_type == "sms.created":
                return await self._process_sms_created(event_data)

            else:
                return {
                    "status": "ignored",
                    "reason": f"Unknown event type: {event_type}",
                    "event_type": event_type,
                }

        except (UserSyncError, ClerkAuthenticationError) as e:
            raise WebhookProcessingError(f"Failed to process {event_type}: {str(e)}")
        except Exception as e:
            raise WebhookProcessingError(
                f"Unexpected error processing {event_type}: {str(e)}"
            )

    async def _process_user_created(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Process user.created webhook - sync user directly"""
        try:
            clerk_user_id = user_data.get("id")
            if not clerk_user_id:
                raise WebhookProcessingError("User ID missing from creation event")

            # Sync user directly instead of scheduling task
            sync_result = await self.user_sync_service.sync_user_from_clerk(user_data)

            return {
                "status": "success",
                "action": "user_created",
                "clerk_user_id": clerk_user_id,
                "sync_result": sync_result,
                "message": f"User {clerk_user_id} synced successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(f"User creation sync failed: {str(e)}")

    async def _process_user_updated(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Process user.updated webhook - sync user directly"""
        try:
            clerk_user_id = user_data.get("id")
            if not clerk_user_id:
                raise WebhookProcessingError("User ID missing from update event")

            # Sync user directly instead of scheduling task
            sync_result = await self.user_sync_service.sync_user_from_clerk(user_data)

            return {
                "status": "success",
                "action": "user_updated",
                "clerk_user_id": clerk_user_id,
                "sync_result": sync_result,
                "message": f"User {clerk_user_id} synced successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(f"User update sync failed: {str(e)}")

    async def _process_user_deleted(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Process user.deleted webhook - delete user directly"""
        try:
            clerk_user_id = user_data.get("id")
            if not clerk_user_id:
                raise WebhookProcessingError("User ID missing from deletion event")

            # Delete user directly instead of scheduling task
            deleted = self.user_sync_service.delete_user_by_clerk_id(clerk_user_id)

            return {
                "status": "success",
                "action": "user_deleted",
                "clerk_user_id": clerk_user_id,
                "deleted": deleted,
                "message": f"User {clerk_user_id} deleted successfully"
                if deleted
                else f"User {clerk_user_id} not found for deletion",
            }

        except Exception as e:
            raise WebhookProcessingError(f"User deletion failed: {str(e)}")

    # ===== ORGANIZATION WEBHOOK PROCESSING =====
    async def _process_organization_created(
        self, org_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process organization.created webhook - for MatchBot B2B teams.

        For: Corporate teams, matchmaker agencies, enterprise clients
        """
        try:
            org_id = org_data.get("id")
            if not org_id:
                raise WebhookProcessingError(
                    "Organization ID missing from creation event"
                )

            # Log organization creation
            logger.info(
                f"Organization created: {org_id} - {org_data.get('name', 'Unknown')}"
            )

            # TODO: Sync organization to local database if needed
            # For now, we rely on Clerk for organization storage

            return {
                "status": "processed",
                "action": "organization_created",
                "organization_id": org_id,
                "organization_name": org_data.get("name"),
                "message": "Organization created successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Organization creation processing failed: {str(e)}"
            )

    async def _process_organization_updated(
        self, org_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process organization.updated webhook"""
        try:
            org_id = org_data.get("id")
            if not org_id:
                raise WebhookProcessingError(
                    "Organization ID missing from update event"
                )

            logger.info(f"Organization updated: {org_id}")

            return {
                "status": "processed",
                "action": "organization_updated",
                "organization_id": org_id,
                "message": "Organization updated successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Organization update processing failed: {str(e)}"
            )

    async def _process_organization_deleted(
        self, org_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process organization.deleted webhook"""
        try:
            org_id = org_data.get("id")
            if not org_id:
                raise WebhookProcessingError(
                    "Organization ID missing from deletion event"
                )

            logger.info(f"Organization deleted: {org_id}")

            # TODO: Clean up related data in local database

            return {
                "status": "processed",
                "action": "organization_deleted",
                "organization_id": org_id,
                "message": "Organization deleted successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Organization deletion processing failed: {str(e)}"
            )

    async def _process_organization_membership_created(
        self, membership_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process organizationMembership.created webhook.

        For MatchBot B2B: User joins corporate team/matchmaker agency
        """
        try:
            org_id = membership_data.get("organization", {}).get("id")
            user_id = membership_data.get("public_user_data", {}).get("user_id")

            if not org_id or not user_id:
                raise WebhookProcessingError(
                    "Organization or user ID missing from membership event"
                )

            logger.info(f"User {user_id} joined organization {org_id}")

            # TODO: Update local user organization membership if needed

            return {
                "status": "processed",
                "action": "membership_created",
                "organization_id": org_id,
                "user_id": user_id,
                "message": "Organization membership created successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Organization membership creation processing failed: {str(e)}"
            )

    async def _process_organization_membership_deleted(
        self, membership_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process organizationMembership.deleted webhook"""
        try:
            org_id = membership_data.get("organization", {}).get("id")
            user_id = membership_data.get("public_user_data", {}).get("user_id")

            if not org_id or not user_id:
                raise WebhookProcessingError(
                    "Organization or user ID missing from membership event"
                )

            logger.info(f"User {user_id} left organization {org_id}")

            return {
                "status": "processed",
                "action": "membership_deleted",
                "organization_id": org_id,
                "user_id": user_id,
                "message": "Organization membership deleted successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Organization membership deletion processing failed: {str(e)}"
            )

    async def _process_organization_membership_updated(
        self, membership_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process organizationMembership.updated webhook"""
        try:
            org_id = membership_data.get("organization", {}).get("id")
            user_id = membership_data.get("public_user_data", {}).get("user_id")

            logger.info(
                f"Organization membership updated: user {user_id} in org {org_id}"
            )

            return {
                "status": "processed",
                "action": "membership_updated",
                "organization_id": org_id,
                "user_id": user_id,
                "message": "Organization membership updated successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Organization membership update processing failed: {str(e)}"
            )

    # ===== SESSION WEBHOOK PROCESSING =====
    async def _process_session_created(
        self, session_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process session.created webhook - track user logins"""
        try:
            session_id = session_data.get("id")
            user_id = session_data.get("user_id")

            logger.info(f"Session created: {session_id} for user {user_id}")

            # TODO: Track user login analytics if needed

            return {
                "status": "processed",
                "action": "session_created",
                "session_id": session_id,
                "user_id": user_id,
                "message": "Session created successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(
                f"Session creation processing failed: {str(e)}"
            )

    async def _process_session_ended(
        self, session_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process session.ended webhook - track user logouts"""
        try:
            session_id = session_data.get("id")
            user_id = session_data.get("user_id")

            logger.info(f"Session ended: {session_id} for user {user_id}")

            return {
                "status": "processed",
                "action": "session_ended",
                "session_id": session_id,
                "user_id": user_id,
                "message": "Session ended successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(f"Session end processing failed: {str(e)}")

    # ===== EMAIL/SMS WEBHOOK PROCESSING =====
    async def _process_email_created(
        self, email_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process email.created webhook - track email sending"""
        try:
            email_id = email_data.get("id")
            to_email = email_data.get("to_email_address")
            email_type = email_data.get("slug")  # e.g., "welcome_email"

            logger.info(f"Email sent: {email_type} to {to_email}")

            # TODO: Track email metrics if needed

            return {
                "status": "processed",
                "action": "email_created",
                "email_id": email_id,
                "email_type": email_type,
                "message": "Email creation processed successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(f"Email creation processing failed: {str(e)}")

    async def _process_sms_created(self, sms_data: dict[str, Any]) -> dict[str, Any]:
        """Process sms.created webhook - track SMS sending"""
        try:
            sms_id = sms_data.get("id")
            to_phone = sms_data.get("to_phone_number")
            sms_type = sms_data.get("slug")  # e.g., "verification_code"

            logger.info(f"SMS sent: {sms_type} to {to_phone}")

            return {
                "status": "processed",
                "action": "sms_created",
                "sms_id": sms_id,
                "sms_type": sms_type,
                "message": "SMS creation processed successfully",
            }

        except Exception as e:
            raise WebhookProcessingError(f"SMS creation processing failed: {str(e)}")

    def _get_webhook_by_id(self, session: Session, webhook_id: str) -> WebhookEvent:
        """Get existing webhook event by ID"""
        from sqlmodel import select

        statement = select(WebhookEvent).where(WebhookEvent.webhook_id == webhook_id)
        result = session.exec(statement)
        return result.first()

    def _create_webhook_event(
        self,
        session: Session,
        webhook_id: str,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
    ) -> WebhookEvent:
        """Create new webhook event record"""
        webhook_event = WebhookEvent(
            webhook_id=webhook_id,
            event_type=webhook_data.get("type", "unknown"),
            status=WebhookStatus.PENDING,
            raw_data=webhook_data,
            source_ip=headers.get("x-forwarded-for", headers.get("x-real-ip")),
            user_agent=headers.get("user-agent"),
            created_at=datetime.now(timezone.utc),
        )

        session.add(webhook_event)
        session.commit()
        session.refresh(webhook_event)

        return webhook_event


def validate_webhook_signature(payload: str, headers: dict[str, str]) -> bool:
    """Validate webhook signature - use ClerkService.verify_webhook_signature instead"""
    clerk_service = ClerkService()
    return clerk_service.verify_webhook_signature(payload, headers)


class WebhookProcessor:
    """Generic webhook processor wrapper"""

    def __init__(self):
        self.clerk_processor = ClerkWebhookProcessor()

    async def process(self, webhook_data: dict[str, Any]) -> dict[str, Any]:
        """Process webhook - simplified interface for tests"""
        return await self.clerk_processor.process_webhook(webhook_data)


class WebhookStatusManager:
    """Manage webhook status transitions with validation"""

    def transition_status(
        self, from_status: WebhookStatus, to_status: WebhookStatus
    ) -> bool:
        """Safely transition webhook status"""
        if not WebhookStateMachine.can_transition(from_status, to_status):
            raise WebhookTransitionError(from_status, to_status)
        return True

    def get_retryable_webhooks(self, session: Session) -> list[WebhookEvent]:
        """Get webhooks that are eligible for retry"""
        from sqlmodel import select

        now = datetime.now(timezone.utc)
        statement = (
            select(WebhookEvent)
            .where(WebhookEvent.status == WebhookStatus.FAILED)
            .where(WebhookEvent.retry_count < WebhookEvent.max_retries)
            .where(WebhookEvent.next_retry_at <= now)
        )

        result = session.exec(statement)
        return result.all()
