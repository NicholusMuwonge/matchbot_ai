import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class WebhookStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    IGNORED = "ignored"
    INVALID = "invalid"


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

    clerk_user_id: str | None = Field(default=None, unique=True, index=True)
    auth_provider: str = Field(default="local")
    is_synced: bool = Field(default=False)
    email_verified: bool = Field(default=False)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    profile_image_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = Field(default=None)
    account_id: int | None = Field(default=None)


class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


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


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


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
