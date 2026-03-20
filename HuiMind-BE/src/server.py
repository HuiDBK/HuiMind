"""FastAPI server bootstrap."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from py_tools.connections.db.mysql import DBManager

from src.dao import init_orm, init_orm_tables, init_redis
from src.routes import api_router
from src.services.bootstrap import BootstrapService

logger = logging.getLogger(__name__)


async def startup():
    db_client = await init_orm()
    await init_orm_tables(db_client)
    await BootstrapService().seed_initial_data()
    try:
        await init_redis()
    except Exception as exc:  # pragma: no cover - redis is optional for the current MVP bootstrap
        logger.warning("Redis init skipped: %s", exc)


async def shutdown():
    logger.info("Shutting down server")
    # await DBManager.DB_CLIENT.db_engine.dispose()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Lifespan context manager started")
    # await startup()
    yield
    await shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="HuiMind API",
        summary="HuiMind MVP API",
        description="HuiMind MVP 后端接口文档，统一使用 /api/v1 前缀，当前接口已切换为正式 ORM 表驱动。",
        version="0.1.0",
        contact={"name": "HuiMind"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
