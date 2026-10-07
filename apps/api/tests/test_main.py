from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_websocket_sends_connection_ready_envelope() -> None:
    with client.websocket_connect("/ws") as websocket:
        assert websocket.receive_json() == {
            "version": 1,
            "type": "connection.ready",
            "payload": {},
        }
