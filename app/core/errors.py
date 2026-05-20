"""Standardized error handling for RelayForge.

Provides structured error responses and global exception handlers
following RFC 7807 Problem Details conventions.
"""

from __future__ import annotations

import traceback
from typing import Any
from uuid import UUID

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------


class RelayForgeError(Exception):
    """Base exception for all RelayForge domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(RelayForgeError):
    def __init__(self, resource: str, resource_id: str | UUID | None = None) -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(
            message=detail,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "resource_id": str(resource_id) if resource_id else None},
        )


class ConflictError(RelayForgeError):
    def __init__(self, message: str = "Resource already exists") -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
        )


class RateLimitError(RelayForgeError):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message="Rate limit exceeded",
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after_seconds": retry_after},
        )


class BadRequestError(RelayForgeError):
    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {},
        )


class UnauthorizedError(RelayForgeError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenError(RelayForgeError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


# ---------------------------------------------------------------------------
# Error response builder
# ---------------------------------------------------------------------------


def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> ORJSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        body["error"]["details"] = details
    if request_id:
        body["error"]["request_id"] = request_id
    return ORJSONResponse(status_code=status_code, content=body)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(RelayForgeError)
    async def relay_forge_error_handler(request: Request, exc: RelayForgeError) -> ORJSONResponse:
        request_id = request.headers.get("x-request-id")
        return _build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details if exc.details else None,
            request_id=request_id,
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> ORJSONResponse:
        request_id = request.headers.get("x-request-id")
        return _build_error_response(
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=str(exc.detail),
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        request_id = request.headers.get("x-request-id")
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", ""),
                    "type": error.get("type", ""),
                }
            )
        return _build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": errors},
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
        request_id = request.headers.get("x-request-id")
        logger.error(
            "unhandled_exception",
            error=str(exc),
            traceback=traceback.format_exc(),
            request_id=request_id,
        )
        return _build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            request_id=request_id,
        )
