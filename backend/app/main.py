import logging

import sentry_sdk
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.api.middleware.auth import AuthMiddleware
from app.api.middleware.authorization import AuthorizationMiddleware
from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Suppress uvicorn access logs for health check 404s
uvicorn_access_logger = logging.getLogger("uvicorn.access")


class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        # Filter out health-check 404 logs from uvicorn access logs
        try:
            # Get the formatted log message
            message = (
                record.getMessage()
                if hasattr(record, "getMessage")
                else str(record.msg)
            )

            # Filter out health-check 404 logs
            if "health-check" in message and "404 Not Found" in message:
                return False

            # Filter out various health-check patterns
            if "/api/v1/utils/health-check/" in message and "404" in message:
                return False

        except Exception:
            # If anything goes wrong, don't filter (safer)
            pass

        return True


# Apply filter to uvicorn access logger
uvicorn_access_logger.addFilter(HealthCheckFilter())

# Also try to suppress INFO level for uvicorn.access specifically for health checks
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())


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
            "script-src 'self' 'unsafe-inline' https://js.clerk.dev https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
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


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all incoming requests and responses
    """

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "NO_ORIGIN")
        user_agent = request.headers.get("user-agent", "NO_USER_AGENT")
        auth_header = request.headers.get("authorization", "NO_AUTH_HEADER")

        # Skip detailed logging for health check endpoints but still log basic info
        if "/health" not in str(request.url):
            logger.info(f"🔍 Request: {request.method} {request.url}")
            logger.info(f"🔍 Origin: {origin}")
            logger.info(f"🔍 User-Agent: {user_agent}")
            logger.info(
                f"🔍 Auth Header: {auth_header[:50]}..."
                if auth_header != "NO_AUTH_HEADER"
                else "🔍 Auth Header: NONE"
            )
        else:
            # Minimal logging for health checks
            logger.debug(f"Health check: {request.method} {request.url}")

        # Check if origin is in allowed CORS origins
        if origin != "NO_ORIGIN" and hasattr(settings, "all_cors_origins"):
            if origin not in settings.all_cors_origins:
                logger.warning(
                    f"⚠️ POTENTIAL CORS ISSUE: Origin '{origin}' not in allowed origins: {settings.all_cors_origins}"
                )

        # Log request body for non-GET requests (be careful with sensitive data)
        if request.method != "GET":
            body = await request.body()
            if body:
                logger.info(f"🔍 Body: {body.decode()[:200]}...")  # Limit body logging

        try:
            response = await call_next(request)

            # Skip logging for health check endpoints
            if "/health" not in str(request.url):
                # Log detailed info for error responses
                if response.status_code >= 400:
                    logger.error(
                        f"❌ Error Response: {response.status_code} for {request.method} {request.url}"
                    )
                    logger.error(f"❌ Request Origin: {origin}")
                    logger.error(f"❌ Auth present: {auth_header != 'NO_AUTH_HEADER'}")
                else:
                    logger.info(f"✅ Success Response: {response.status_code}")

            return response
        except Exception as e:
            logger.error(f"❌ Exception in request processing: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            raise


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
    # Add security schemes for Swagger UI
    openapi_components={
        "securitySchemes": {
            "ClerkAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Enter your Clerk session token. "
                    "Get token from: /api/v1/swagger-auth/get-token-from-browser"
                ),
            }
        }
    },
    # Add security to all endpoints by default
    dependencies=[],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    origin = request.headers.get("origin", "NO_ORIGIN")
    auth_header = request.headers.get("authorization", "NO_AUTH_HEADER")

    logger.error("❌ 422 VALIDATION ERROR DETAILS:")
    logger.error(f"❌ URL: {request.method} {request.url}")
    logger.error(f"❌ Origin: {origin}")
    logger.error(f"❌ Auth Header Present: {auth_header != 'NO_AUTH_HEADER'}")
    logger.error(f"❌ User Agent: {request.headers.get('user-agent', 'UNKNOWN')}")
    logger.error(f"❌ Content-Type: {request.headers.get('content-type', 'UNKNOWN')}")
    logger.error(f"❌ Request headers: {dict(request.headers)}")
    logger.error(f"❌ Validation errors: {exc.errors()}")
    logger.error(f"❌ Request body: {exc.body}")

    # Check for common issues
    errors = exc.errors()
    for error in errors:
        if "Authorization" in str(error):
            logger.error(f"❌ POSSIBLE AUTH DEPENDENCY ISSUE: {error}")
        if "missing" in str(error).lower():
            logger.error(f"❌ MISSING PARAMETER/HEADER: {error}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": f"Request validation failed: {exc.errors()}",
            "body": str(exc.body) if exc.body else None,
            "url": str(request.url),
            "method": request.method,
            "origin": origin,
            "auth_present": auth_header != "NO_AUTH_HEADER",
        },
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    logger.error(f"❌ Pydantic Validation Error on {request.method} {request.url}")
    logger.error(f"❌ Request headers: {dict(request.headers)}")
    logger.error(f"❌ Pydantic validation errors: {exc.errors()}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": f"Data validation failed: {exc.errors()}",
            "url": str(request.url),
            "method": request.method,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"❌ HTTP Exception {exc.status_code} on {request.method} {request.url}"
    )
    logger.error(f"❌ Request headers: {dict(request.headers)}")
    logger.error(f"❌ Exception detail: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "url": str(request.url),
            "method": request.method,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ General Exception on {request.method} {request.url}")
    logger.error(f"❌ Request headers: {dict(request.headers)}")
    logger.error(f"❌ Exception: {str(exc)}")
    logger.error(f"❌ Exception type: {type(exc).__name__}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "url": str(request.url),
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )


# Add authorization middleware (runs AFTER authentication)
app.add_middleware(AuthorizationMiddleware)

# Add authentication middleware (BEFORE request logging so auth data is available for logs)
app.add_middleware(AuthMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Enhanced CORS configuration for Clerk integration
logger.info(f"🔧 CORS Origins configured: {settings.all_cors_origins}")
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
            # Test authentication header
            "X-Test-Role",
        ],
        expose_headers=[
            "X-Total-Count",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        max_age=86400,  # 24 hours
    )
else:
    logger.warning("⚠️ No CORS origins configured - this may cause CORS issues")

app.include_router(api_router, prefix=settings.API_V1_STR)
