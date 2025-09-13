import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from sqlmodel import Session

from app.api.deps import ClerkSessionUser, get_db
from app.models import UserPublic
from app.services.users import UserService

router = APIRouter(prefix="/users", tags=["users"])

# Security scheme for Swagger UI
security = HTTPBearer()

logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=dict,
    summary="Get Users with Clerk Authentication",
    description="Retrieve a paginated list of users. Requires a valid Clerk Bearer token.",
    responses={
        200: {"description": "List of users retrieved successfully"},
        401: {"description": "Authentication failed - invalid or expired token"},
        500: {"description": "Internal server error"},
    },
    dependencies=[Security(security)],
)
def read_users(
    current_user: ClerkSessionUser,  # noqa: ARG001
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_db),
) -> Any:
    """
    Retrieve users with authentication handled by middleware.
    """
    try:
        count, users = UserService.get_users_with_pagination(session, skip, limit)

        return {
            "users": [UserPublic.model_validate(user).model_dump() for user in users],
            "count": count,
            "skip": skip,
            "limit": limit,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
