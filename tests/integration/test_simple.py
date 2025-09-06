"""Simple test to verify mock server isolation with in-memory TestClient."""

from fastapi.testclient import TestClient
from tests.mock_server import MockYouTrackServer

def test_mock_server_starts_automatically():
    """Test that each test gets a fresh server instance with 1 comment and 1 attachment."""
    server = MockYouTrackServer()
    client = TestClient(server.app)
    response = client.get("/issues/TEST-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TEST-1"
    assert data["summary"] == "Test Issue"
    print(f"Response data: {data}")
    assert "comments" in data
    assert "attachments" in data
    assert len(data["comments"]) == 1
    assert len(data["attachments"]) == 1
