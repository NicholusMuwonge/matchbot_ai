from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_db
from app.api.test_auth import setup_test_users
from app.core.config import settings

router = APIRouter(prefix="/dev", tags=["development"])


class TestSetupResponse(BaseModel):
    status: str
    actions: list[str] = []
    instructions: list[str] = []
    reason: str = ""


@router.post("/setup-test-users", response_model=TestSetupResponse)
async def setup_test_users_endpoint(session: Annotated[Session, Depends(get_db)]) -> TestSetupResponse:
    """
    Create test users for authentication testing.

    Only available when ENABLE_AUTH_TESTING=true.
    Creates users with different roles for testing protected endpoints without Clerk API usage.
    """
    if not settings.ENABLE_AUTH_TESTING:
        raise HTTPException(
            status_code=403,
            detail="Test authentication is not enabled. Set ENABLE_AUTH_TESTING=true",
        )

    result = await setup_test_users(session)

    return TestSetupResponse(
        status=result["status"],
        actions=result.get("actions", []),
        instructions=result.get("instructions", []),
        reason=result.get("reason", ""),
    )


@router.get("/test-auth-info")
async def test_auth_info() -> dict[str, Any]:
    """
    Get information about test authentication setup.
    """
    if not settings.ENABLE_AUTH_TESTING:
        return {
            "enabled": False,
            "message": "Test authentication is disabled. Set ENABLE_AUTH_TESTING=true to enable.",
        }

    return {
        "enabled": True,
        "message": "Test authentication is ENABLED",
        "usage": {
            "setup": "Call POST /api/v1/dev/setup-test-users first",
            "headers": {"X-Test-Role": "regular_user | platform_admin | app_owner"},
            "swagger_instructions": [
                "1. Go to Swagger UI at http://localhost:8000/docs",
                "2. Click 'Authorize' button (if visible) or use custom headers",
                "3. Add header: X-Test-Role with value: regular_user, platform_admin, or app_owner",
                "4. Test protected endpoints with different roles",
            ],
        },
        "test_users": {
            "regular_user": "test-regular@example.com",
            "platform_admin": "test-admin@example.com",
            "app_owner": "test-owner@example.com",
        },
    }
