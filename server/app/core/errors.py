import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import request_id

log = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AppError(Exception):
    def __init__(
        self, code: str, status: int, message: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message
        self.details = details or {}


def invalid_token() -> AppError:
    return AppError("invalid_token", 401, "Missing, wrong or expired token.")


def invalid_credentials() -> AppError:
    return AppError("invalid_credentials", 401, "Wrong credentials.")


def forbidden() -> AppError:
    return AppError("forbidden", 403, "You do not have access to this case.")


def case_not_found() -> AppError:
    return AppError("case_not_found", 404, "Case not found.")


def too_many_attempts(minutes: int) -> AppError:
    return AppError(
        "too_many_attempts", 429, "Too many attempts. Try again later.", {"minutes": minutes}
    )


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details or {})
    ).model_dump()


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            error_body("validation_error", "Invalid input.", {"errors": errors}), status_code=422
        )

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        # The request id lets support find the full traceback in the logs.
        log.exception("unhandled error")
        return JSONResponse(
            error_body(
                "internal_error",
                "Something went wrong. Please try again.",
                {"request_id": request_id.get()},
            ),
            status_code=500,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(error_body(code, str(exc.detail)), status_code=exc.status_code)
