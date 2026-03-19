"""Route registry."""

from fastapi import APIRouter

from src.routes.api_v1 import router as api_v1_router

api_router = APIRouter()
api_router.include_router(api_v1_router, prefix="/api/v1")
