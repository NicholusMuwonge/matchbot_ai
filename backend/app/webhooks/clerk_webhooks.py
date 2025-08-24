import json
from datetime import datetime, timedelta
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
from app.services.user_sync_service import UserSyncError
from app.tasks.user_sync_tasks import (
    schedule_user_delete,
    schedule_user_sync,
)


class WebhookProcessingError(Exception):
    pass


async def process_clerk_webhook(
    webhook_data: dict[str, Any], headers: dict[str, str], session: Session = None
) -> dict[str, Any]:
    processor = ClerkWebhookProcessor()
    return await processor.process_webhook_with_verification(
        webhook_data, headers, session
    )


class ClerkWebhookProcessor:
    def __init__(self):
        self.clerk_service = ClerkService()

    async def process_webhook_with_verification(
        self,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
        session: Session = None,
    ) -> dict[str, Any]:
        webhook_id = headers.get("svix-id", f"webhook_{datetime.utcnow().isoformat()}")
        payload_str = json.dumps(webhook_data, sort_keys=True)

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
            webhook_event.processed_at = datetime.utcnow()
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
            webhook_event.next_retry_at = datetime.utcnow() + timedelta(
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
        """Process user.created webhook - schedule background user sync"""
        try:
            clerk_user_id = user_data.get("id")
            if not clerk_user_id:
                raise WebhookProcessingError("User ID missing from creation event")
            task_id = schedule_user_sync(user_data, delay_seconds=0)

            return {
                "status": "accepted",
                "action": "user_created",
                "clerk_user_id": clerk_user_id,
                "task_id": task_id,
                "message": "User sync scheduled for background processing",
            }

        except Exception as e:
            raise WebhookProcessingError(f"User creation scheduling failed: {str(e)}")

    async def _process_user_updated(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Process user.updated webhook - schedule background user sync"""
        try:
            clerk_user_id = user_data.get("id")
            if not clerk_user_id:
                raise WebhookProcessingError("User ID missing from update event")
            task_id = schedule_user_sync(user_data, delay_seconds=0)

            return {
                "status": "accepted",
                "action": "user_updated",
                "clerk_user_id": clerk_user_id,
                "task_id": task_id,
                "message": "User sync scheduled for background processing",
            }

        except Exception as e:
            raise WebhookProcessingError(f"User update scheduling failed: {str(e)}")

    async def _process_user_deleted(self, user_data: dict[str, Any]) -> dict[str, Any]:
        """Process user.deleted webhook - schedule background user deletion"""
        try:
            clerk_user_id = user_data.get("id")
            if not clerk_user_id:
                raise WebhookProcessingError("User ID missing from deletion event")
            task_id = schedule_user_delete(clerk_user_id, delay_seconds=0)

            return {
                "status": "accepted",
                "action": "user_deleted",
                "clerk_user_id": clerk_user_id,
                "task_id": task_id,
                "message": "User deletion scheduled for background processing",
            }

        except Exception as e:
            raise WebhookProcessingError(f"User deletion scheduling failed: {str(e)}")

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
            created_at=datetime.utcnow(),
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

        now = datetime.utcnow()
        statement = (
            select(WebhookEvent)
            .where(WebhookEvent.status == WebhookStatus.FAILED)
            .where(WebhookEvent.retry_count < WebhookEvent.max_retries)
            .where(WebhookEvent.next_retry_at <= now)
        )

        result = session.exec(statement)
        return result.all()
