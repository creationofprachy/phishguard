from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] in {"ok", "degraded"}


def test_dashboard_served_at_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "PhishGuard" in res.text


def test_predict_valid_url():
    res = client.post("/api/predict", json={"url": "https://www.example.com"})
    assert res.status_code == 200
    body = res.json()
    assert body["verdict"] in {"Legitimate", "Suspicious", "Phishing"}


def test_predict_empty_url_returns_400():
    res = client.post("/api/predict", json={"url": ""})
    assert res.status_code in (400, 422)


def test_predict_url_with_whitespace_rejected():
    res = client.post("/api/predict", json={"url": "http://example.com/ path"})
    assert res.status_code in (400, 422)


def test_predict_missing_field_returns_422():
    res = client.post("/api/predict", json={})
    assert res.status_code == 422


def test_history_lifecycle():
    client.delete("/api/history")
    empty = client.get("/api/history").json()
    assert empty["count"] == 0

    client.post("/api/predict", json={"url": "https://www.example.com"})
    after = client.get("/api/history").json()
    assert after["count"] == 1

    client.delete("/api/history")
    cleared = client.get("/api/history").json()
    assert cleared["count"] == 0


def test_metrics_endpoint():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    assert "selected_model" in res.json()
