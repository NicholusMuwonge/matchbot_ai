"""
Main models module - imports all models from the models package.
This file is kept for backward compatibility and to maintain existing import paths.
"""

# Import all models from the organized models package
from app.models.base import Message, NewPassword, Token, TokenPayload
from app.models.item import (
    Item,
    ItemBase,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)
from app.models.user import (
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
from app.models.webhook import (
    WebhookEvent,
    WebhookStateMachine,
    WebhookStatus,
    WebhookTransitionError,
)

# Export all models for backward compatibility
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
    # Webhook models
    "WebhookEvent",
    "WebhookStateMachine",
    "WebhookStatus",
    "WebhookTransitionError",
]
