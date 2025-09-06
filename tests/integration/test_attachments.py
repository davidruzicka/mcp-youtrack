"""Test binary attachment upload with automatically running mock server."""

import tempfile
import os
from fastapi.testclient import TestClient
from tests.mock_server import MockYouTrackServer


def test_upload_text_attachment():
    """Test uploading text attachment using in-memory TestClient."""
    server = MockYouTrackServer()
    client = TestClient(server.app)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is test attachment content\nWith multiple lines\n")
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as file_data:
            files = {'file': (os.path.basename(temp_file_path), file_data, 'text/plain')}
            response = client.post("/issues/TEST-1/attachments", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["id"]
        assert data["name"] == os.path.basename(temp_file_path)
        assert data["size"] > 0
        # Check that the attachment is listed on the issue
        issue_resp = client.get("/issues/TEST-1")
        assert issue_resp.status_code == 200
        issue = issue_resp.json()
        assert any(att["name"] == os.path.basename(temp_file_path) for att in issue["attachments"])
    finally:
        os.unlink(temp_file_path)


def test_upload_binary_attachment():
    """Test uploading binary attachment using in-memory TestClient."""
    server = MockYouTrackServer()
    client = TestClient(server.app)
    binary_content = b'\x00\x01\x02\x03Binary content\xFF\xFE'
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
        f.write(binary_content)
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as file_data:
            files = {'file': (os.path.basename(temp_file_path), file_data, 'application/octet-stream')}
            response = client.post("/issues/TEST-1/attachments", files=files)
        assert response.status_code == 200
        data = response.json()
        assert data["id"]
        assert data["size"] == len(binary_content)
        # Check that the attachment is listed on the issue
        issue_resp = client.get("/issues/TEST-1")
        assert issue_resp.status_code == 200
        issue = issue_resp.json()
        assert any(att["name"] == os.path.basename(temp_file_path) for att in issue["attachments"])
    finally:
        os.unlink(temp_file_path)


def test_full_issue_workflow():
    """Test complete workflow with issue, comments and attachments using in-memory TestClient."""
    server = MockYouTrackServer()
    client = TestClient(server.app)
    # 1. Get initial issue state
    issue_resp = client.get("/issues/TEST-1")
    assert issue_resp.status_code == 200
    issue = issue_resp.json()
    initial_comments = len(issue["comments"])
    initial_attachments = len(issue["attachments"])

    # 2. Add comment
    comment_resp = client.post("/issues/TEST-1/comments", json={"text": "Integration test comment"})
    assert comment_resp.status_code == 200
    comment = comment_resp.json()
    assert comment is not None
    assert comment["text"] == "Integration test comment"

    # 3. Upload attachment
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Integration test attachment")
        temp_file_path = f.name
    try:
        with open(temp_file_path, 'rb') as file_data:
            files = {'file': (os.path.basename(temp_file_path), file_data, 'text/plain')}
            attach_resp = client.post("/issues/TEST-1/attachments", files=files)
        assert attach_resp.status_code == 200
        attachment = attach_resp.json()
        assert attachment is not None
        # 4. Verify changes
        updated_issue_resp = client.get("/issues/TEST-1")
        assert updated_issue_resp.status_code == 200
        updated_issue = updated_issue_resp.json()
        assert len(updated_issue["comments"]) == initial_comments + 1
        assert len(updated_issue["attachments"]) == initial_attachments + 1
    finally:
        os.unlink(temp_file_path)
