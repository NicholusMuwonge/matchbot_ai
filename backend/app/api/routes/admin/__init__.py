from fastapi import APIRouter

from .clerk import router as clerk_router
from .rbac import router as rbac_router

router = APIRouter()
router.include_router(clerk_router, tags=["admin-clerk"])
router.include_router(rbac_router, tags=["admin-rbac"])