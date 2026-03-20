"""Base handler definitions."""

from src.data_schemas.api_schemas.base import ApiResponse, PageData


class BaseHandler:
    @staticmethod
    def success(data=None) -> ApiResponse:
        return ApiResponse(data={} if data is None else data)

    @staticmethod
    def page(*, total: int, data_list: list) -> ApiResponse:
        return ApiResponse(data=PageData(total=total, data_list=data_list))
