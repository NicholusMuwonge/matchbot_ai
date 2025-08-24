"""
Webhook model factories - like Ruby Factory Bot
Clean test data generation for WebhookEvent models
"""

from datetime import timedelta

import factory
from factory import Faker, LazyAttribute, Sequence

from app.models import WebhookEvent, WebhookStatus


class WebhookEventFactory(factory.Factory):
    """Factory for creating WebhookEvent models in tests"""

    class Meta:
        model = WebhookEvent

    # Unique webhook identifiers
    webhook_id = Sequence(lambda n: f"msg_test_{n:06d}")
    event_type = "user.created"
    status = WebhookStatus.PENDING

    # Processing tracking
    processed_at = None
    retry_count = 0
    max_retries = 3
    next_retry_at = None

    # Error tracking (initially None)
    error_message = None
    error_details = None

    # Timestamps
    created_at = Faker("date_time_this_year", tzinfo=None)
    updated_at = None

    # Request metadata
    source_ip = Faker("ipv4")
    user_agent = "Svix-Webhooks/1.24"

    # Webhook data (basic structure)
    raw_data = LazyAttribute(
        lambda obj: {
            "type": obj.event_type,
            "object": "event",
            "data": {
                "id": "user_test_123456",
                "object": "user",
                "email_addresses": [
                    {
                        "email_address": "test@example.com",
                        "verification": {"status": "verified"},
                    }
                ],
                "first_name": "Test",
                "last_name": "User",
            },
        }
    )
    processed_data = None


class ProcessingWebhookFactory(WebhookEventFactory):
    """Factory for webhook currently being processed"""

    status = WebhookStatus.PROCESSING
    updated_at = Faker("date_time_this_year", tzinfo=None)


class SuccessfulWebhookFactory(WebhookEventFactory):
    """Factory for successfully processed webhook"""

    status = WebhookStatus.SUCCESS
    processed_at = Faker("date_time_this_year", tzinfo=None)
    updated_at = LazyAttribute(lambda obj: obj.processed_at)
    processed_data = LazyAttribute(
        lambda obj: {"user_created": True, "user_id": obj.raw_data["data"]["id"]}
    )


class FailedWebhookFactory(WebhookEventFactory):
    """Factory for failed webhook (for retry testing)"""

    status = WebhookStatus.FAILED
    retry_count = 1
    next_retry_at = LazyAttribute(lambda obj: obj.created_at + timedelta(minutes=5))
    error_message = "Database connection error"
    error_details = LazyAttribute(
        lambda obj: {
            "error_type": "DatabaseError",
            "retry_attempt": obj.retry_count,
            "original_error": obj.error_message,
        }
    )
    updated_at = Faker("date_time_this_year", tzinfo=None)


class InvalidWebhookFactory(WebhookEventFactory):
    """Factory for webhook with invalid signature"""

    status = WebhookStatus.INVALID
    error_message = "Invalid webhook signature"
    processed_at = Faker("date_time_this_year", tzinfo=None)


class IgnoredWebhookFactory(WebhookEventFactory):
    """Factory for ignored webhook (unknown event type)"""

    event_type = "session.created"  # Unknown event type
    status = WebhookStatus.IGNORED
    processed_at = Faker("date_time_this_year", tzinfo=None)
    raw_data = LazyAttribute(
        lambda obj: {
            "type": obj.event_type,
            "object": "event",
            "data": {"id": "session_123", "unknown_field": "value"},
        }
    )


# Specific Clerk event factories
class UserCreatedWebhookFactory(WebhookEventFactory):
    """Factory for user.created webhook events"""

    event_type = "user.created"


class UserUpdatedWebhookFactory(WebhookEventFactory):
    """Factory for user.updated webhook events"""

    event_type = "user.updated"


class UserDeletedWebhookFactory(WebhookEventFactory):
    """Factory for user.deleted webhook events"""

    event_type = "user.deleted"
    raw_data = LazyAttribute(
        lambda obj: {
            "type": "user.deleted",
            "object": "event",
            "data": {
                "id": f"user_deleted_{factory.Faker('random_int', min=100000, max=999999).generate({})}",
                "object": "user",
                "deleted": True,
            },
        }
    )


# Webhook traits (like Ruby Factory Bot traits)
class WebhookTraits:
    """Common webhook variations for tests"""

    @staticmethod
    def with_webhook_id(webhook_id: str):
        """Webhook with specific webhook ID"""
        return WebhookEventFactory(webhook_id=webhook_id)

    @staticmethod
    def user_created(user_id: str = None, email: str = None):
        """User created webhook with specific data"""
        user_id = (
            user_id
            or f"user_test_{factory.Faker('random_int', min=100000, max=999999).generate({})}"
        )
        email = email or factory.Faker("email").generate({})

        return UserCreatedWebhookFactory(
            raw_data={
                "type": "user.created",
                "object": "event",
                "data": {
                    "id": user_id,
                    "object": "user",
                    "email_addresses": [
                        {"email_address": email, "verification": {"status": "verified"}}
                    ],
                    "first_name": factory.Faker("first_name").generate({}),
                    "last_name": factory.Faker("last_name").generate({}),
                },
            }
        )

    @staticmethod
    def processing():
        """Webhook currently being processed"""
        return ProcessingWebhookFactory()

    @staticmethod
    def successful():
        """Successfully processed webhook"""
        return SuccessfulWebhookFactory()

    @staticmethod
    def failed(retry_count: int = 1):
        """Failed webhook with specific retry count"""
        return FailedWebhookFactory(retry_count=retry_count)

    @staticmethod
    def invalid():
        """Invalid webhook (bad signature)"""
        return InvalidWebhookFactory()

    @staticmethod
    def ignored():
        """Ignored webhook (unknown event)"""
        return IgnoredWebhookFactory()
