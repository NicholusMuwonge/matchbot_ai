import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select

from app.api.deps import ClerkSessionUser, get_db, require_role
from app.models import (
    Item,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
    Message,
    User,
)

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=ItemsPublic)
def read_my_items(
    session: Annotated[Session, Depends(get_db)], current_user: ClerkSessionUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Get items owned by current user.
    """
    count_statement = (
        select(func.count()).select_from(Item).where(Item.owner_id == current_user.id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Item).where(Item.owner_id == current_user.id).offset(skip).limit(limit)
    )
    items = session.exec(statement).all()
    return ItemsPublic(data=items, count=count)


@router.get("/admin/all", response_model=ItemsPublic)
def read_all_items(
    session: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))], skip: int = 0, limit: int = 100
) -> Any:
    """
    Admin-only: Get all items in system.
    """
    count_statement = select(func.count()).select_from(Item)
    count = session.exec(count_statement).one()
    statement = select(Item).offset(skip).limit(limit)
    items = session.exec(statement).all()
    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_my_item(
    session: Annotated[Session, Depends(get_db)], current_user: ClerkSessionUser, id: uuid.UUID
) -> Any:
    """
    Get item by ID (must be owned by current user).
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item


@router.get("/admin/{id}", response_model=ItemPublic)
def read_any_item(session: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))], id: uuid.UUID) -> Any:
    """
    Admin-only: Get any item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: Annotated[Session, Depends(get_db)], current_user: ClerkSessionUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_my_item(
    *,
    session: Annotated[Session, Depends(get_db)],
    current_user: ClerkSessionUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item owned by current user.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/admin/{id}", response_model=ItemPublic)
def update_any_item(
    *,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Admin-only: Update any item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_my_item(
    session: Annotated[Session, Depends(get_db)], current_user: ClerkSessionUser, id: uuid.UUID
) -> Message:
    """
    Delete an item owned by current user.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")


@router.delete("/admin/{id}")
def delete_any_item(session: Annotated[Session, Depends(get_db)], _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))], id: uuid.UUID) -> Message:
    """
    Admin-only: Delete any item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
