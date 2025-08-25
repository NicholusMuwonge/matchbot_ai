import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers for production
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (adjust as needed for your frontend)
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.clerk.dev; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.clerk.dev https://api.clerk.com; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        # HSTS (only in production with HTTPS)
        if settings.ENVIRONMENT != "local":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # Additional security headers
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), bluetooth=(), magnetometer=(), "
            "gyroscope=(), speaker=(), vibrate=(), fullscreen=()"
        )

        return response


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Enhanced CORS configuration for Clerk integration
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Mx-ReqToken",
            "Keep-Alive",
            "X-Requested-With",
            "If-Modified-Since",
            # Clerk-specific headers
            "clerk-session-id",
            "clerk-user-id",
            "clerk-publishable-key",
        ],
        expose_headers=[
            "X-Total-Count",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=86400,  # 24 hours
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
