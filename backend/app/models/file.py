import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Text, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel, select, text

from app.tasks.file.process_file import process_uploaded_file

if TYPE_CHECKING:
    from app.models.user import User


class FileStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    SYNCING = "syncing"
    SYNCED = "synced"
    EXTRACTED = "extracted"
    FAILED = "failed"


class StorageProvider(str, Enum):
    MINIO = "minio"
    S3 = "s3"


class FileBase(SQLModel):
    external_id: str = Field(max_length=255, unique=True, index=True)
    filename: str = Field(max_length=255, index=True)
    storage_path: str = Field(sa_column=Column(Text, nullable=False))
    content_type: str = Field(max_length=100)
    file_size_bytes: int = Field(sa_column=Column(BigInteger, nullable=False))
    file_hash: str | None = Field(default=None, max_length=64, unique=True, index=True)
    provider: StorageProvider = Field(default=StorageProvider.MINIO)
    status: FileStatus = Field(default=FileStatus.PENDING, index=True)
    failure_reason: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )


class File(FileBase, table=True):
    __tablename__ = "files"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)

    content: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    file_metadata: dict | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
    )
    expires_at: datetime | None = Field(default=None)

    user: "User" = Relationship(back_populates="files")

    @classmethod
    def by_external_ids(cls, external_ids: list[str], user_id: uuid.UUID):
        return select(cls).where(
            cls.external_id.in_(external_ids), cls.user_id == user_id
        )

    def __repr__(self):
        return (
            f"<File(id={self.id}, filename='{self.filename}', "
            f"status={self.status}, user_id={self.user_id})>"
        )



class FileCreate(FileBase):
    user_id: uuid.UUID
    content: dict | None = None
    file_metadata: dict | None = None


class FileUpdate(SQLModel):
    filename: str | None = None
    status: FileStatus | None = None
    content: dict | None = None
    failure_reason: str | None = None
    file_metadata: dict | None = None


class FilePublic(FileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    content: dict | None
    file_metadata: dict | None
    created_at: datetime
    updated_at: datetime


class FilesPublic(SQLModel):
    data: list[FilePublic]
    count: int


from sqlalchemy import inspect


@event.listens_for(File, "after_update")
def process_uploaded_file_on_status_change(_mapper, _connection, target):
    """Queue file processing when status changes to UPLOADED."""
    state = inspect(target)
    status_history = state.attrs.status.history

    if status_history.has_changes() and target.status == FileStatus.UPLOADED:
        process_uploaded_file.delay(str(target.id))
