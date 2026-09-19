from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded


def error_body(request: Request, status_code: int, message: str, details: Any = None) -> dict:
    error = {"code": str(status_code), "message": message, "request_id": getattr(request.state, "request_id", None)}
    if details is not None:
        error["details"] = details
    return {"error": error}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(status_code=exc.status_code, content=error_body(request, exc.status_code, message), headers=exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=error_body(request, 422, "Validation failed", jsonable_encoder(exc.errors())))


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content=error_body(request, 429, "Too many requests"))
