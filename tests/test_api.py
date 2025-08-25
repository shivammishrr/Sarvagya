from fastapi.testclient import TestClient
from src.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_stream_starts():
    client = TestClient(app)
    # Ensure the streaming endpoint initializes successfully
    payload = {"user_query": "test"}
    headers = {"Accept": "text/event-stream"}
    with client.stream("POST", "/api/chat/stream", json=payload, headers=headers) as resp:
        assert resp.status_code == 200
