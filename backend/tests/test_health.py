"""Exercise the HTTP contract without a running server or external provider."""

from fastapi.testclient import TestClient
from policysim.main import app


def test_health_contract() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"status": "ok", "service": "policysim"}


def test_health_is_read_only() -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/health").status_code == 405


def test_unknown_api_does_not_look_successful() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/forecasts").status_code == 404


def test_openapi_exposes_versioned_health_contract() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    response_schema = schema["paths"]["/api/v1/health"]["get"]["responses"]["200"]
    assert response_schema["content"]["application/json"]["schema"]["$ref"].endswith(
        "/HealthResponse"
    )
