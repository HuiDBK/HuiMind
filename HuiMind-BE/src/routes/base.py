"""Base router definitions."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter


class BaseAPIRouter(APIRouter):
    def register(self, path: str, endpoint, **kwargs) -> None:
        self.add_api_route(path, endpoint, **kwargs)

    def get(self, path: str, endpoint: Callable[..., Any], **kwargs) -> None:
        self.add_api_route(path, endpoint, methods=["GET"], **kwargs)

    def post(self, path: str, endpoint: Callable[..., Any], **kwargs) -> None:
        self.add_api_route(path, endpoint, methods=["POST"], **kwargs)

    def put(self, path: str, endpoint: Callable[..., Any], **kwargs) -> None:
        self.add_api_route(path, endpoint, methods=["PUT"], **kwargs)

    def delete(self, path: str, endpoint: Callable[..., Any], **kwargs) -> None:
        self.add_api_route(path, endpoint, methods=["DELETE"], **kwargs)
