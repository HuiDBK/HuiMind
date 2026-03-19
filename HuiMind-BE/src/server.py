"""FastAPI server bootstrap."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="HuiMind API",
        summary="HuiMind MVP Mock API",
        description="HuiMind MVP 后端接口文档，当前阶段使用 Mock 数据返回，统一使用 /api/v1 前缀。",
        version="0.1.0",
        contact={"name": "HuiMind"},
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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
