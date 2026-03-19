"""FastAPI application entrypoint."""

from src.server import app


if __name__ == "__main__":
    import uvicorn

    from src.settings.base_setting import server_host, server_log_level, server_port

    uvicorn.run("main:app", host=server_host, port=server_port, reload=True, log_level=server_log_level)
