from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import require_role
from app.models import User
from app.services.clerk_auth import ClerkAuthenticationError, ClerkService

router = APIRouter()


class SignInTokenCreate(BaseModel):
    user_id: str
    expires_in_seconds: int | None = None


class SignInTokenResponse(BaseModel):
    token: str
    user_id: str
    status: str
    url: str | None = None
    expires_at: int | None = None


class JWTTemplateCreate(BaseModel):
    name: str
    claims: dict[str, Any]
    lifetime: int | None = None
    allowed_clock_skew: int | None = None


class JWTTemplateResponse(BaseModel):
    id: str
    name: str
    claims: dict[str, Any]
    lifetime: int | None = None
    created_at: int | None = None


class OAuthTokenVerify(BaseModel):
    token: str


class OAuthTokenResponse(BaseModel):
    valid: bool
    user_id: str | None = None
    client_id: str | None = None
    scopes: list[str] | None = None
    expires_at: int | None = None


@router.post("/sign-in-tokens", response_model=SignInTokenResponse)
async def create_sign_in_token(
    token_data: SignInTokenCreate,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> SignInTokenResponse:
    try:
        clerk_service = ClerkService()
        result = clerk_service.create_sign_in_token(
            user_id=token_data.user_id, expires_in_seconds=token_data.expires_in_seconds
        )

        if not result:
            raise HTTPException(
                status_code=500, detail="Failed to create sign-in token"
            )

        return SignInTokenResponse(
            token=result["token"],
            user_id=result["user_id"],
            status=result["status"],
            url=result["url"],
            expires_at=result["expires_at"],
        )

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create sign-in token: {str(e)}"
        )


@router.post("/jwt-templates", response_model=JWTTemplateResponse)
async def create_jwt_template(
    template_data: JWTTemplateCreate,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> JWTTemplateResponse:
    try:
        clerk_service = ClerkService()
        result = clerk_service.create_jwt_template(
            name=template_data.name,
            claims=template_data.claims,
            lifetime=template_data.lifetime,
            allowed_clock_skew=template_data.allowed_clock_skew,
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create JWT template")

        return JWTTemplateResponse(
            id=result["id"],
            name=result["name"],
            claims=result["claims"],
            lifetime=result["lifetime"],
            created_at=result["created_at"],
        )

    except ClerkAuthenticationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create JWT template: {str(e)}"
        )


@router.post("/oauth/verify", response_model=OAuthTokenResponse)
async def verify_oauth_token(
    token_data: OAuthTokenVerify,
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> OAuthTokenResponse:
    try:
        clerk_service = ClerkService()
        result = clerk_service.verify_oauth_token(token_data.token)

        if not result:
            return OAuthTokenResponse(valid=False)

        return OAuthTokenResponse(
            valid=result["valid"],
            user_id=result["user_id"],
            client_id=result["client_id"],
            scopes=result["scopes"],
            expires_at=result["expires_at"],
        )

    except ClerkAuthenticationError:
        return OAuthTokenResponse(valid=False)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to verify OAuth token: {str(e)}"
        )


@router.get("/health")
async def admin_health_check(
    _: Annotated[User, Depends(require_role(["app_owner", "platform_admin"]))],
) -> dict[str, str]:
    try:
        clerk_service = ClerkService()

        if clerk_service.client:
            return {"status": "healthy", "service": "clerk"}
        else:
            return {"status": "unhealthy", "service": "clerk"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
