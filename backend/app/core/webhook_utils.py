"""
Shared webhook utilities for consistent webhook processing across the application.

This module provides reusable webhook processing patterns to reduce duplication.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session

from app.core.db import engine
from app.models import WebhookEvent, WebhookStatus


class WebhookProcessorMixin:
    """Mixin class providing common webhook processing utilities."""

    @staticmethod
    def generate_webhook_id(headers: dict[str, str]) -> str:
        """Generate consistent webhook ID from headers."""
        return headers.get(
            "svix-id", f"webhook_{datetime.now(timezone.utc).isoformat()}"
        )

    @staticmethod
    def create_webhook_event(
        webhook_id: str,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
        session: Session,
    ) -> WebhookEvent:
        """Create standardized webhook event record."""
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

    @staticmethod
    def update_webhook_success(
        webhook_event: WebhookEvent, result: dict[str, Any], session: Session
    ) -> None:
        """Update webhook event to successful status."""
        webhook_event.status = WebhookStatus.SUCCESS
        webhook_event.processed_at = datetime.now(timezone.utc)
        webhook_event.processed_data = result
        session.commit()

    @staticmethod
    def update_webhook_failure(
        webhook_event: WebhookEvent, error: Exception, session: Session
    ) -> None:
        """Update webhook event to failed status with retry logic."""
        webhook_event.status = WebhookStatus.FAILED
        webhook_event.error_message = str(error)
        webhook_event.retry_count += 1
        retry_delay_minutes = min(2**webhook_event.retry_count, 60)
        webhook_event.next_retry_at = datetime.now(timezone.utc) + timedelta(
            minutes=retry_delay_minutes
        )
        session.commit()

    @staticmethod
    def format_webhook_response(
        webhook_id: str, result: dict[str, Any], processed_at: datetime = None
    ) -> dict[str, Any]:
        """Format consistent webhook response."""
        return {
            **result,
            "webhook_id": webhook_id,
            "processed_at": (processed_at or datetime.now(timezone.utc)).isoformat(),
        }

    @staticmethod
    def format_error_response(webhook_id: str, error_message: str) -> dict[str, Any]:
        """Format consistent error response."""
        return {
            "status": "failed",
            "webhook_id": webhook_id,
            "error": error_message,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }


class WebhookEventHandler:
    """Base class for webhook event processing with common patterns."""

    def __init__(self):
        self.processor = WebhookProcessorMixin()

    async def process_with_error_handling(
        self,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
        session: Session = None,
    ) -> dict[str, Any]:
        """Process webhook with standardized error handling and session management."""
        webhook_id = self.processor.generate_webhook_id(headers)

        if session is None:
            with Session(engine) as session:
                return await self._process_with_session(
                    webhook_data, headers, webhook_id, session
                )
        else:
            return await self._process_with_session(
                webhook_data, headers, webhook_id, session
            )

    async def _process_with_session(
        self,
        webhook_data: dict[str, Any],
        headers: dict[str, str],
        webhook_id: str,
        session: Session,
    ) -> dict[str, Any]:
        """Template method for session-based webhook processing."""
        webhook_event = self.processor.create_webhook_event(
            webhook_id, webhook_data, headers, session
        )

        try:
            # Process the actual webhook logic
            result = await self.process_webhook_logic(webhook_data)

            # Update success status
            self.processor.update_webhook_success(webhook_event, result, session)

            return self.processor.format_webhook_response(
                webhook_id, result, webhook_event.processed_at
            )

        except Exception as e:
            # Update failure status
            self.processor.update_webhook_failure(webhook_event, e, session)

            return self.processor.format_error_response(webhook_id, str(e))

    async def process_webhook_logic(
        self, webhook_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Override this method in subclasses to implement specific webhook logic."""
        raise NotImplementedError("Subclasses must implement process_webhook_logic")
