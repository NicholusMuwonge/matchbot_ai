"""
Webhook routes for Clerk integration
Handles incoming webhooks from Clerk for user events
"""

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.webhooks.clerk_webhooks import process_clerk_webhook

router = APIRouter()


class WebhookResponse(BaseModel):
    status: str
    webhook_id: str | None = None
    message: str | None = None
    task_id: str | None = None
    error: str | None = None
    processed_at: str | None = None


@router.post("/clerk", response_model=WebhookResponse)
async def handle_clerk_webhook(
    request: Request,
    session: SessionDep,
    svix_id: str = Header(None, alias="svix-id"),
    svix_timestamp: str = Header(None, alias="svix-timestamp"),
    svix_signature: str = Header(None, alias="svix-signature"),
) -> WebhookResponse:
    """
    Handle incoming Clerk webhooks

    Processes user.created, user.updated, and user.deleted events
    Verifies webhook signature and processes events in background
    """
    try:
        # Get the webhook payload
        payload = await request.json()

        # Prepare headers for signature verification
        headers = {
            "svix-id": svix_id or "",
            "svix-timestamp": svix_timestamp or "",
            "svix-signature": svix_signature or "",
        }

        # Validate required headers
        if not all([svix_id, svix_timestamp, svix_signature]):
            raise HTTPException(
                status_code=400,
                detail="Missing required webhook headers (svix-id, svix-timestamp, svix-signature)",
            )

        # Process the webhook
        result = await process_clerk_webhook(payload, headers, session)

        return WebhookResponse(
            status=result["status"],
            webhook_id=result.get("webhook_id"),
            message=result.get("message"),
            task_id=result.get("task_id"),
            processed_at=result.get("processed_at"),
            error=result.get("error"),
        )

    except Exception as e:
        return WebhookResponse(status="failed", error=str(e))


@router.get("/status/{webhook_id}")
async def get_webhook_status(webhook_id: str, session: SessionDep) -> dict[str, Any]:
    """
    Get the status of a specific webhook processing
    """
    try:
        from sqlmodel import select

        from app.models import WebhookEvent

        statement = select(WebhookEvent).where(WebhookEvent.webhook_id == webhook_id)
        webhook_event = session.exec(statement).first()

        if not webhook_event:
            raise HTTPException(status_code=404, detail="Webhook not found")

        return {
            "webhook_id": webhook_event.webhook_id,
            "status": webhook_event.status,
            "event_type": webhook_event.event_type,
            "created_at": webhook_event.created_at.isoformat(),
            "processed_at": webhook_event.processed_at.isoformat()
            if webhook_event.processed_at
            else None,
            "retry_count": webhook_event.retry_count,
            "error_message": webhook_event.error_message,
            "next_retry_at": webhook_event.next_retry_at.isoformat()
            if webhook_event.next_retry_at
            else None,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failed")
async def get_failed_webhooks(session: SessionDep, limit: int = 50) -> dict[str, Any]:
    """
    Get list of failed webhooks that might need manual intervention
    """
    try:
        from sqlmodel import select

        from app.models import WebhookEvent, WebhookStatus

        statement = (
            select(WebhookEvent)
            .where(WebhookEvent.status == WebhookStatus.FAILED)
            .limit(limit)
        )

        failed_webhooks = session.exec(statement).all()

        return {
            "failed_webhooks": [
                {
                    "webhook_id": webhook.webhook_id,
                    "event_type": webhook.event_type,
                    "created_at": webhook.created_at.isoformat(),
                    "retry_count": webhook.retry_count,
                    "error_message": webhook.error_message,
                    "raw_data": webhook.raw_data,
                }
                for webhook in failed_webhooks
            ],
            "count": len(failed_webhooks),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{webhook_id}")
async def retry_failed_webhook(webhook_id: str, session: SessionDep) -> WebhookResponse:
    """
    Manually retry a failed webhook processing
    """
    try:
        from sqlmodel import select

        from app.models import WebhookEvent, WebhookStatus
        from app.webhooks.clerk_webhooks import process_clerk_webhook

        statement = select(WebhookEvent).where(WebhookEvent.webhook_id == webhook_id)
        webhook_event = session.exec(statement).first()

        if not webhook_event:
            raise HTTPException(status_code=404, detail="Webhook not found")

        if webhook_event.status != WebhookStatus.FAILED:
            raise HTTPException(
                status_code=400,
                detail=f"Webhook is in {webhook_event.status} state, can only retry failed webhooks",
            )

        if webhook_event.retry_count >= webhook_event.max_retries:
            raise HTTPException(
                status_code=400,
                detail=f"Webhook has reached maximum retries ({webhook_event.max_retries})",
            )

        # Reconstruct headers from stored data (if available)
        headers = {
            "svix-id": webhook_event.webhook_id,
            "svix-timestamp": str(int(webhook_event.created_at.timestamp())),
            "svix-signature": "manual_retry",  # Skip signature verification for manual retry
        }

        # Process the webhook again
        result = await process_clerk_webhook(webhook_event.raw_data, headers, session)

        return WebhookResponse(
            status=result["status"],
            webhook_id=webhook_id,
            message="Webhook retry initiated",
            task_id=result.get("task_id"),
            processed_at=result.get("processed_at"),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_webhook_stats(session: SessionDep) -> dict[str, Any]:
    """
    Get webhook processing statistics
    """
    try:
        from datetime import datetime, timedelta

        from sqlmodel import func, select

        from app.models import WebhookEvent, WebhookStatus

        # Get stats for last 24 hours
        since = datetime.utcnow() - timedelta(days=1)

        # Total webhooks
        total_statement = select(func.count(WebhookEvent.id)).where(
            WebhookEvent.created_at >= since
        )
        total_webhooks = session.exec(total_statement).first() or 0

        # Success rate
        success_statement = select(func.count(WebhookEvent.id)).where(
            WebhookEvent.created_at >= since,
            WebhookEvent.status == WebhookStatus.SUCCESS,
        )
        successful_webhooks = session.exec(success_statement).first() or 0

        # Failed webhooks
        failed_statement = select(func.count(WebhookEvent.id)).where(
            WebhookEvent.created_at >= since,
            WebhookEvent.status == WebhookStatus.FAILED,
        )
        failed_webhooks = session.exec(failed_statement).first() or 0

        # Processing webhooks
        processing_statement = select(func.count(WebhookEvent.id)).where(
            WebhookEvent.created_at >= since,
            WebhookEvent.status == WebhookStatus.PROCESSING,
        )
        processing_webhooks = session.exec(processing_statement).first() or 0

        success_rate = (
            (successful_webhooks / total_webhooks * 100) if total_webhooks > 0 else 0
        )

        return {
            "period": "24_hours",
            "total_webhooks": total_webhooks,
            "successful_webhooks": successful_webhooks,
            "failed_webhooks": failed_webhooks,
            "processing_webhooks": processing_webhooks,
            "success_rate": round(success_rate, 2),
            "stats_timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
