from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test GET /health endpoint for all response fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "construction-site-management"
    assert data["version"] == "1.0.0"
