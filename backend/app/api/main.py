from fastapi import APIRouter

from app.api.routes import auth, swagger_auth, users
from app.core.config import settings

api_router = APIRouter()

# Core routes
api_router.include_router(users.router)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Development/Testing routes (only in non-production)
if settings.ENVIRONMENT != "production":
    api_router.include_router(swagger_auth.router)

# Temporarily disable other routes due to missing dependencies
# api_router.include_router(utils.router)
# api_router.include_router(login.router)
# api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
# api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
# api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
# api_router.include_router(items.router)


# Temporarily disable all conditional routes
# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)

# Development routes for testing (only when test auth is enabled)
# if settings.ENABLE_AUTH_TESTING:
#     api_router.include_router(dev.router)
