import uuid
from datetime import datetime

from sqlmodel import JSON, Field, Relationship, SQLModel


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    display_name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] = Field(default_factory=list, sa_type=JSON)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None)

    user_roles: list["UserRole"] = Relationship(back_populates="role")

    def has_permission(self, permission: str) -> bool:
        if not isinstance(self.permissions, list):
            return False

        if "*" in self.permissions:
            return True

        if permission in self.permissions:
            return True

        for perm in self.permissions:
            if perm.endswith(":*") and permission.startswith(perm[:-1]):
                return True

        return False

    def add_permission(self, permission: str) -> None:
        if not isinstance(self.permissions, list):
            self.permissions = []

        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now()

    def remove_permission(self, permission: str) -> None:
        if isinstance(self.permissions, list) and permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now()


class UserRole(SQLModel, table=True):
    __tablename__ = "user_roles"

    id: int = Field(primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    role_id: int = Field(foreign_key="roles.id")
    assigned_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    assigned_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)

    role: Role = Relationship(back_populates="user_roles")

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired
