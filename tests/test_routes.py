import pytest
from collections.abc import Iterator
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_ready(client: TestClient) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code in (200, 503)


def test_rfc7807_error(client: TestClient) -> None:
    response = client.get("/api/v1/nonexistent-route-for-testing")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "message" in data["error"]
