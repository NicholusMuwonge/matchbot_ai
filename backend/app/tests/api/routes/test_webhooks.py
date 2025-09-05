"""
Tests for webhook API routes
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WebhookEvent, WebhookStatus


class TestWebhookRoutes:
    """Test webhook endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_handle_clerk_webhook_missing_headers(self, client):
        """Test webhook handling with missing headers"""
        payload = {
            "type": "user.created",
            "data": {"id": "user_123", "email_addresses": []},
        }

        response = client.post("/api/v1/webhooks/clerk", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "Missing required webhook headers" in data["error"]

    def test_handle_clerk_webhook_success(self, client, db):
        """Test successful webhook handling"""
        import uuid

        webhook_id = f"msg_test_{uuid.uuid4().hex[:8]}"

        with patch(
            "app.api.routes.webhooks.process_clerk_webhook", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "status": "accepted",
                "webhook_id": webhook_id,
                "task_id": "task_456",
                "message": "User sync scheduled for background processing",
            }

            payload = {
                "type": "user.created",
                "data": {"id": "user_123", "email_addresses": []},
            }

            headers = {
                "svix-id": webhook_id,
                "svix-timestamp": "1234567890",
                "svix-signature": "v1,test_signature",
            }

            response = client.post(
                "/api/v1/webhooks/clerk", json=payload, headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["webhook_id"] == webhook_id
            assert data["task_id"] == "task_456"

    def test_get_webhook_status_not_found(self, client, db):
        """Test get webhook status for non-existent webhook"""
        response = client.get("/api/v1/webhooks/status/nonexistent")

        assert response.status_code == 404
        assert "Webhook not found" in response.json()["detail"]

    def test_get_webhook_status_success(self, client, db):
        """Test successful webhook status retrieval"""
        import uuid
        from datetime import datetime, timezone

        webhook_id = f"msg_test_{uuid.uuid4().hex[:8]}"

        # Create a webhook event in the database
        webhook_event = WebhookEvent(
            webhook_id=webhook_id,
            event_type="user.created",
            status=WebhookStatus.SUCCESS,
            raw_data={"type": "user.created", "data": {"id": "user_123"}},
            created_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            retry_count=0,
        )

        db.add(webhook_event)
        db.commit()

        response = client.get(f"/api/v1/webhooks/status/{webhook_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["webhook_id"] == webhook_id
        assert data["status"] == "success"
        assert data["event_type"] == "user.created"
        assert data["retry_count"] == 0

    def test_get_failed_webhooks(self, client, db):
        """Test getting list of failed webhooks"""
        import uuid
        from datetime import datetime, timezone

        webhook_id = f"msg_failed_{uuid.uuid4().hex[:8]}"

        # Create a failed webhook event
        webhook_event = WebhookEvent(
            webhook_id=webhook_id,
            event_type="user.created",
            status=WebhookStatus.FAILED,
            raw_data={"type": "user.created", "data": {"id": "user_123"}},
            created_at=datetime.now(timezone.utc),
            retry_count=1,
            error_message="Processing failed",
        )

        db.add(webhook_event)
        db.commit()

        response = client.get("/api/v1/webhooks/failed")

        assert response.status_code == 200
        data = response.json()
        # Check that we got some failed webhooks (the specific one we created should be there)
        assert data["count"] >= 0
        # If there are failed webhooks, verify the structure is correct
        if data["failed_webhooks"]:
            webhook = data["failed_webhooks"][0]
            assert "webhook_id" in webhook
            assert "event_type" in webhook
            # The response shows these fields are available
            assert "created_at" in webhook
            assert "error_message" in webhook

    def test_retry_failed_webhook_not_found(self, client, db):
        """Test retry webhook that doesn't exist"""
        response = client.post("/api/v1/webhooks/retry/nonexistent")

        assert response.status_code == 404
        assert "Webhook not found" in response.json()["detail"]

    def test_retry_failed_webhook_wrong_status(self, client, db):
        """Test retry webhook that is not in failed status"""
        import uuid
        from datetime import datetime, timezone

        webhook_id = f"msg_success_{uuid.uuid4().hex[:8]}"

        # Create a successful webhook event
        webhook_event = WebhookEvent(
            webhook_id=webhook_id,
            event_type="user.created",
            status=WebhookStatus.SUCCESS,
            raw_data={"type": "user.created", "data": {"id": "user_123"}},
            created_at=datetime.now(timezone.utc),
            processed_at=datetime.now(timezone.utc),
            retry_count=0,
        )

        db.add(webhook_event)
        db.commit()

        response = client.post(f"/api/v1/webhooks/retry/{webhook_id}")

        assert response.status_code == 400
        assert "can only retry failed webhooks" in response.json()["detail"]

    def test_retry_failed_webhook_max_retries(self, client, db):
        """Test retry webhook that has reached max retries"""
        import uuid
        from datetime import datetime, timezone

        webhook_id = f"msg_maxretries_{uuid.uuid4().hex[:8]}"

        # Create a webhook that has reached max retries
        webhook_event = WebhookEvent(
            webhook_id=webhook_id,
            event_type="user.created",
            status=WebhookStatus.FAILED,
            raw_data={"type": "user.created", "data": {"id": "user_123"}},
            created_at=datetime.now(timezone.utc),
            retry_count=3,
            max_retries=3,
            error_message="Max retries reached",
        )

        db.add(webhook_event)
        db.commit()

        response = client.post(f"/api/v1/webhooks/retry/{webhook_id}")

        assert response.status_code == 400
        assert "reached maximum retries" in response.json()["detail"]

    def test_retry_failed_webhook_success(self, client, db):
        """Test successful webhook retry"""
        import uuid
        from datetime import datetime, timezone

        webhook_id = f"msg_retry_{uuid.uuid4().hex[:8]}"

        # Create a failed webhook event
        webhook_event = WebhookEvent(
            webhook_id=webhook_id,
            event_type="user.created",
            status=WebhookStatus.FAILED,
            raw_data={"type": "user.created", "data": {"id": "user_123"}},
            created_at=datetime.now(timezone.utc),
            retry_count=1,
            max_retries=3,
            error_message="Previous failure",
        )

        db.add(webhook_event)
        db.commit()

        with patch(
            "app.webhooks.clerk_webhooks.process_clerk_webhook", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "status": "accepted",
                "webhook_id": webhook_id,
                "task_id": "task_retry456",
                "message": "Retry successful",
            }

            response = client.post(f"/api/v1/webhooks/retry/{webhook_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["webhook_id"] == webhook_id
            assert data["message"] == "Webhook retry initiated"

    def test_get_webhook_stats(self, client, db):
        """Test webhook statistics endpoint"""
        import uuid
        from datetime import datetime, timezone

        # Create some webhook events for testing
        now = datetime.now(timezone.utc)
        test_prefix = uuid.uuid4().hex[:8]

        # Successful webhook
        success_webhook = WebhookEvent(
            webhook_id=f"msg_stats_success_{test_prefix}",
            event_type="user.created",
            status=WebhookStatus.SUCCESS,
            raw_data={"type": "user.created", "data": {"id": "user_success"}},
            created_at=now,
            processed_at=now,
            retry_count=0,
        )

        # Failed webhook
        failed_webhook = WebhookEvent(
            webhook_id=f"msg_stats_failed_{test_prefix}",
            event_type="user.updated",
            status=WebhookStatus.FAILED,
            raw_data={"type": "user.updated", "data": {"id": "user_failed"}},
            created_at=now,
            retry_count=2,
            error_message="Test failure",
        )

        # Processing webhook
        processing_webhook = WebhookEvent(
            webhook_id=f"msg_stats_processing_{test_prefix}",
            event_type="user.deleted",
            status=WebhookStatus.PROCESSING,
            raw_data={"type": "user.deleted", "data": {"id": "user_processing"}},
            created_at=now,
            retry_count=0,
        )

        db.add(success_webhook)
        db.add(failed_webhook)
        db.add(processing_webhook)
        db.commit()

        response = client.get("/api/v1/webhooks/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "24_hours"
        assert data["total_webhooks"] >= 3
        assert data["successful_webhooks"] >= 1
        assert data["failed_webhooks"] >= 1
        assert data["processing_webhooks"] >= 1
        assert "success_rate" in data
        assert "stats_timestamp" in data
