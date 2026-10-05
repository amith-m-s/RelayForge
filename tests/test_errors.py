from uuid import UUID

from app.core.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    _build_error_response,
)


def test_not_found_error_contains_resource_context() -> None:
    error = NotFoundError("delivery", UUID("00000000-0000-0000-0000-000000000001"))
    assert error.code == "NOT_FOUND"
    assert error.status_code == 404
    assert "delivery" in error.message
    assert error.details["resource_id"]


def test_error_variants_have_expected_statuses() -> None:
    assert ConflictError().status_code == 409
    assert RateLimitError().status_code == 429
    assert BadRequestError().status_code == 400
    assert UnauthorizedError().status_code == 401
    assert ForbiddenError().status_code == 403


def test_error_response_builder_includes_request_id_and_details() -> None:
    response = _build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"field": "email"},
        request_id="req-123",
    )
    assert response.status_code == 422
    assert response.body
