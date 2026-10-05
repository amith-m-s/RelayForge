from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import NotFoundError, register_exception_handlers


class Payload(BaseModel):
    email: str


def build_test_app() -> FastAPI:
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError("delivery", "delivery-1")

    @test_app.get("/http-error")
    async def http_error() -> None:
        raise HTTPException(status_code=403, detail="forbidden")

    @test_app.post("/validation")
    async def validation(payload: Payload) -> dict[str, str]:
        return payload.model_dump()

    @test_app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("boom")

    return test_app


def test_custom_exception_handler() -> None:
    with TestClient(build_test_app()) as client:
        response = client.get("/not-found")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_http_exception_handler() -> None:
    with TestClient(build_test_app()) as client:
        response = client.get("/http-error")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "HTTP_ERROR"


def test_validation_exception_handler() -> None:
    with TestClient(build_test_app()) as client:
        response = client.post("/validation", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unhandled_exception_handler() -> None:
    with TestClient(build_test_app(), raise_server_exceptions=False) as client:
        response = client.get("/crash")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
