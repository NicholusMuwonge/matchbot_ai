"""
Webhook models and event handling.
"""

from datetime import datetime
from enum import Enum

from sqlmodel import JSON, Column, Field, SQLModel


class WebhookStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    IGNORED = "ignored"
    INVALID = "invalid"


class WebhookEvent(SQLModel, table=True):
    __tablename__ = "webhook_events"

    id: int = Field(primary_key=True)
    webhook_id: str = Field(unique=True, index=True)
    event_type: str = Field(index=True)
    status: WebhookStatus = Field(default=WebhookStatus.PENDING, index=True)

    processed_at: datetime | None = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    next_retry_at: datetime | None = None
    error_message: str | None = None
    error_details: dict | None = Field(default=None, sa_column=Column(JSON))
    raw_data: dict = Field(sa_column=Column(JSON))
    processed_data: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    source_ip: str | None = None
    user_agent: str | None = None


class WebhookStateMachine:
    VALID_TRANSITIONS: dict[WebhookStatus, set[WebhookStatus]] = {
        WebhookStatus.PENDING: {
            WebhookStatus.PROCESSING,
            WebhookStatus.INVALID,
            WebhookStatus.IGNORED,
        },
        WebhookStatus.PROCESSING: {
            WebhookStatus.SUCCESS,
            WebhookStatus.FAILED,
        },
        WebhookStatus.FAILED: {
            WebhookStatus.PROCESSING,
            WebhookStatus.FAILED,
        },
        WebhookStatus.SUCCESS: set(),
        WebhookStatus.IGNORED: set(),
        WebhookStatus.INVALID: set(),
    }

    @classmethod
    def can_transition(
        cls, from_status: WebhookStatus, to_status: WebhookStatus
    ) -> bool:
        return to_status in cls.VALID_TRANSITIONS.get(from_status, set())

    @classmethod
    def get_valid_next_states(cls, current_status: WebhookStatus) -> set[WebhookStatus]:
        return cls.VALID_TRANSITIONS.get(current_status, set())

    @classmethod
    def is_terminal_state(cls, status: WebhookStatus) -> bool:
        return len(cls.VALID_TRANSITIONS.get(status, set())) == 0


class WebhookTransitionError(Exception):
    def __init__(self, from_status: WebhookStatus, to_status: WebhookStatus):
        super().__init__(
            f"Invalid transition from {from_status.value} to {to_status.value}"
        )
        self.from_status = from_status
        self.to_status = to_status
