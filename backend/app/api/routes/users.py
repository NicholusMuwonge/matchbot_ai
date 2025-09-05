import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, col, delete, func, select

from app import crud
from app.api.deps import (
    ClerkSessionUser,
    get_db,
    require_role,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.user_sync_service import UserSyncError, UserSyncService
from app.utils import generate_new_account_email, send_email


# Clerk Admin Models
class UserSyncResponse(BaseModel):
    status: str
    user_id: str | None = None
    clerk_user_id: str
    action: str
    message: str | None = None


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersPublic)
def read_users(
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


@router.post("/", response_model=UserPublic)
def create_user(
    *,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *,
    session: Annotated[Session, Depends(get_db)],
    user_in: UserUpdateMe,
    current_user: ClerkSessionUser,
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *,
    session: Annotated[Session, Depends(get_db)],
    body: UpdatePassword,
    current_user: ClerkSessionUser,
) -> Any:
    """
    Update own password.
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: ClerkSessionUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(
    session: Annotated[Session, Depends(get_db)], current_user: ClerkSessionUser
) -> Any:
    """
    Delete own user (regular users only - admins cannot delete themselves).
    """
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.delete("/admin/me", response_model=Message)
def delete_admin_user_me(
    _: Annotated[Session, Depends(get_db)],
    __: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> Any:
    """
    Admin users are not allowed to delete themselves for security.
    """
    raise HTTPException(
        status_code=403, detail="Admin users are not allowed to delete themselves"
    )


@router.post("/signup", response_model=UserPublic)
def register_user(
    session: Annotated[Session, Depends(get_db)], user_in: UserRegister
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    current_user: ClerkSessionUser,
) -> Any:
    """
    Get a specific user by id (only yourself).
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user != current_user:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own user information",
        )
    return user


@router.get("/admin/{user_id}", response_model=UserPublic)
def read_any_user_by_id(
    user_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> Any:
    """
    Admin-only: Get any user by id.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserPublic)
def update_user(
    *,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    return db_user


@router.delete("/{user_id}")
def delete_user(
    session: Annotated[Session, Depends(get_db)],
    current_user: ClerkSessionUser,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
    user_id: uuid.UUID,
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)  # type: ignore
    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


# Clerk User Sync Operations (Admin Only)
@router.post(
    "/clerk/sync/{clerk_user_id}",
    response_model=UserSyncResponse,
)
async def sync_user_from_clerk(
    clerk_user_id: str,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> UserSyncResponse:
    """
    Manually trigger user sync from Clerk (Admin only).

    Single responsibility: Sync specific user from Clerk to local database.
    Normally handled by webhooks, but useful for manual admin operations.
    """
    try:
        sync_service = UserSyncService()
        result = await sync_service.fetch_and_sync_user(clerk_user_id)

        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="User not found in Clerk")

        return UserSyncResponse(
            status=result["status"],
            user_id=result.get("user_id"),
            clerk_user_id=clerk_user_id,
            action=result.get("action", "sync"),
            message=f"User {result['status']} successfully",
        )

    except UserSyncError as e:
        raise HTTPException(status_code=500, detail=f"User sync failed: {str(e)}")


@router.post(
    "/clerk/sync-by-email/{email}",
    response_model=UserSyncResponse | Message,
)
async def sync_user_by_email(
    email: str,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> Any:
    """
    Find and sync user by email from Clerk (Admin only).

    Single responsibility: Find user by email in Clerk and sync to local database.
    """
    try:
        sync_service = UserSyncService()
        result = await sync_service.sync_user_by_email(email)

        if result is None:
            return Message(message=f"No user found with email: {email}")

        return UserSyncResponse(
            status=result["status"],
            user_id=result.get("user_id"),
            clerk_user_id=result["clerk_user_id"],
            action=result.get("action", "sync"),
            message=f"User {result['status']} successfully",
        )

    except UserSyncError as e:
        raise HTTPException(status_code=500, detail=f"User sync failed: {str(e)}")


@router.get(
    "/clerk/sync-stats",
)
async def get_clerk_sync_stats(
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> dict[str, int]:
    """
    Get Clerk user synchronization statistics (Admin only).

    Single responsibility: Return sync statistics for monitoring.
    """
    try:
        sync_service = UserSyncService()
        return sync_service.get_sync_stats()

    except UserSyncError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync stats: {str(e)}"
        )
