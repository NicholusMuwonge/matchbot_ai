from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import require_role
from app.models import Message, User
from app.utils import generate_test_email, send_email

from .health import router as health_router

router = APIRouter(prefix="/utils", tags=["utils"])

# Include health check endpoints
router.include_router(health_router)


@router.post(
    "/test-email/",
    status_code=201,
)
def test_email(
    email_to: EmailStr,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
