from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR


class ApiException(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiException)
    async def handle_api_exception(request: Request, exc: ApiException) -> JSONResponse:
        return build_error_response(exc.status_code, exc.message, request.url.path)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return build_error_response(
            HTTP_400_BAD_REQUEST,
            "Solicitud invalida: revise el body enviado",
            request.url.path,
            {"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Error HTTP"
        return build_error_response(exc.status_code, message, request.url.path)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        return build_error_response(
            HTTP_500_INTERNAL_SERVER_ERROR,
            "Error interno del servidor",
            request.url.path,
        )


def build_error_response(
    status_code: int,
    message: str,
    path: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status_code,
        "error": http_error_name(status_code),
        "message": message,
        "path": path,
    }

    if extra:
        payload.update(extra)

    return JSONResponse(status_code=status_code, content=payload)


def http_error_name(status_code: int) -> str:
    names = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        502: "Bad Gateway",
    }
    return names.get(status_code, "HTTP Error")
