import pytest
from fastapi.testclient import TestClient
from tests.mock_server import MockYouTrackServer

def test_get_issue_isolation():
    """Each test gets a fresh server instance with only 1 comment."""
    server = MockYouTrackServer()
    client = TestClient(server.app)
    response = client.get("/issues/TEST-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TEST-1"
    assert len(data["comments"]) == 1
    assert data["comments"][0]["text"] == "Test comment"
    assert len(data["attachments"]) == 1
    assert data["attachments"][0]["name"] == "test-file.txt"

def test_add_comment_isolation():
    """Adding a comment does not affect other tests."""
    server = MockYouTrackServer()
    client = TestClient(server.app)
    # Add comment
    resp = client.post("/issues/TEST-1/comments", json={"text": "Another comment"})
    assert resp.status_code == 200
    # Now get issue
    response = client.get("/issues/TEST-1")
    data = response.json()
    assert len(data["comments"]) == 2
    assert any(c["text"] == "Another comment" for c in data["comments"])
