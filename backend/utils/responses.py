from __future__ import annotations

from math import ceil
from typing import Any

from fastapi.encoders import jsonable_encoder

from backend.core.schemas import ApiError, ApiResponse, PaginationMeta


def success_response(*, message: str, data: Any = None, pagination: PaginationMeta | None = None) -> ApiResponse:
    return ApiResponse(success=True, message=message, data=jsonable_encoder(data), pagination=pagination, error=None)


def paginated_response(*, message: str, data: Any, page: int, page_size: int, total: int) -> ApiResponse:
    total_pages = ceil(total / page_size) if page_size > 0 else 0
    pagination = PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages)
    return success_response(message=message, data=data, pagination=pagination)


def error_response(*, code: str, detail: str, message: str = "Request failed") -> ApiResponse:
    return ApiResponse(success=False, message=message, data=None, pagination=None, error=ApiError(code=code, detail=detail))
