from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_and_catalog_endpoints():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["records"] == 6240
    assert len(client.get("/api/skus").json()["skus"]) == 15
    assert client.get("/api/regions").json()["regions"][0] == "All"


def test_forecast_endpoint_returns_business_outputs():
    response = client.post("/api/forecast", json={"sku_id": "SKU_001", "region": "All", "periods": 4})
    assert response.status_code == 200
    result = response.json()
    assert len(result["forecast"]) == 4
    assert result["stockout"]["risk_level"] in {"critical", "warning", "safe"}
    assert "ensemble" in result["metrics"]

