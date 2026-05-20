from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_ready() -> None:
    # Readiness check performs deep dependency verification.
    # In test environment, DB/Redis may be bypassed or simulated.
    response = client.get("/api/v1/ready")
    # Should return either 200 (if up) or 503 (if degraded)
    assert response.status_code in (200, 503)


def test_rfc7807_error() -> None:
    response = client.get("/api/v1/nonexistent-route-for-testing")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "message" in data["error"]

