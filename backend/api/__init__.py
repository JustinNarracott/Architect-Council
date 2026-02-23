from fastapi import APIRouter

from .routes import router as adr_router
from .codebase_routes import router as codebase_router
from .governance_routes import router as governance_router
from .query_routes import router as query_router

router = APIRouter()
router.include_router(adr_router)
router.include_router(codebase_router)
router.include_router(governance_router)
router.include_router(query_router)

__all__ = ["router"]
