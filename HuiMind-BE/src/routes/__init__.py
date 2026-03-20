"""Route registry."""

from fastapi import APIRouter

from src.routes import auth, buddy, career, dashboard, document, rag, review, scene, system

api_router = APIRouter()
for router in [
    system.router,
    auth.router,
    dashboard.router,
    scene.router,
    document.router,
    rag.router,
    buddy.router,
    review.router,
    career.router,
]:
    api_router.include_router(router)

