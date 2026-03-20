"""System services."""

from src.services.base import BaseService


class SystemService(BaseService):
    async def root(self) -> dict:
        return {"service": "HuiMind API", "version": "v1", "docs": "/docs"}

    async def health(self) -> dict:
        return {"status": "ok"}
