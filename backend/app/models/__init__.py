"""
Models package for the application.
"""

from .base import Message, NewPassword, Token, TokenPayload
from .file import (
    File,
    FileBase,
    FileCreate,
    FilePublic,
    FilesPublic,
    FileStatus,
    FileUpdate,
    StorageProvider,
)
from .item import Item, ItemBase, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from .rbac import Role, UserRole
from .user import (
    UpdatePassword,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from .webhook import (
    WebhookEvent,
    WebhookStateMachine,
    WebhookStatus,
    WebhookTransitionError,
)

__all__ = [
    # Base models
    "Message",
    "NewPassword",
    "Token",
    "TokenPayload",
    # User models
    "UpdatePassword",
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UserRegister",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    # Item models
    "Item",
    "ItemBase",
    "ItemCreate",
    "ItemPublic",
    "ItemsPublic",
    "ItemUpdate",
    # File models
    "File",
    "FileBase",
    "FileCreate",
    "FilePublic",
    "FilesPublic",
    "FileStatus",
    "FileUpdate",
    "StorageProvider",
    # Webhook models
    "WebhookEvent",
    "WebhookStateMachine",
    "WebhookStatus",
    "WebhookTransitionError",
    # RBAC models
    "Role",
    "UserRole",
]
