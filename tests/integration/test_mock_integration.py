"""Integration tests with mock YouTrack server including binary attachments."""

import pytest
import io
import tempfile
import os
from mcp_youtrack.youtrack_client import YouTrackClient

class TestAsyncIntegration:
    """Integration tests with mock YouTrack server."""
    
    def test_get_issue_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        response = client.get("/issues/TEST-1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "TEST-1"
        assert data["summary"] == "Test Issue"
        assert data["description"] == "Test issue description"
        assert "comments" in data
        assert len(data["comments"]) == 1
        assert data["comments"][0]["text"] == "Test comment"
        assert "attachments" in data
        assert len(data["attachments"]) == 1
        assert data["attachments"][0]["name"] == "test-file.txt"
    
    def test_update_issue_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        # Update issue
        update_data = {"summary": "Updated Test Issue", "description": "Updated description"}
        resp = client.post("/issues/TEST-1", json=update_data)
        assert resp.status_code == 200
        # Verify update
        response = client.get("/issues/TEST-1")
        data = response.json()
        assert data["summary"] == "Updated Test Issue"
        assert data["description"] == "Updated description"
    
    def test_update_comment_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        # Update comment
        update_data = {"text": "Updated comment text"}
        resp = client.post("/issues/TEST-1/comments/comment-1", json=update_data)
        assert resp.status_code == 200
        updated_comment = resp.json()
        assert updated_comment["text"] == "Updated comment text"
        assert updated_comment["id"] == "comment-1"
        # Verify update persisted
        response = client.get("/issues/TEST-1")
        data = response.json()
        assert len(data["comments"]) == 1
        assert data["comments"][0]["text"] == "Updated comment text"
    
    def test_add_comment_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        # Add comment
        comment_data = {"text": "New test comment"}
        resp = client.post("/issues/TEST-1/comments", json=comment_data)
        assert resp.status_code == 200
        new_comment = resp.json()
        assert new_comment["text"] == "New test comment"
        assert "id" in new_comment
        # Verify comment was added
        response = client.get("/issues/TEST-1")
        data = response.json()
        assert len(data["comments"]) == 2  # Original + new comment
        assert any(c["text"] == "New test comment" for c in data["comments"])
    
    def test_add_work_item_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        # Add work item
        work_item_data = {
            "duration": {"minutes": 120},
            "description": "Test work item",
            "type": {"name": "Development"}
        }
        resp = client.post("/issues/TEST-1/timeTracking/workItems", json=work_item_data)
        assert resp.status_code == 200
        new_work_item = resp.json()
        assert new_work_item["description"] == "Test work item"
        assert new_work_item["duration"]["minutes"] == 120
        assert "id" in new_work_item
        # Verify work item was added
        response = client.get("/issues/TEST-1/timeTracking/workItems")
        work_items = response.json()
        assert len(work_items) == 1
        assert work_items[0]["description"] == "Test work item"
    
    def test_list_projects_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        response = client.get("/admin/projects")
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 1
        project = projects[0]
        assert project["name"] == "Test Project"
        assert project["shortName"] == "TEST"
        assert project["archived"] is False
    
    def test_error_handling_integration(self):
        from fastapi.testclient import TestClient
        from tests.mock_server import MockYouTrackServer
        server = MockYouTrackServer()
        client = TestClient(server.app)
        # Test 404 error
        response = client.get("/issues/NONEXISTENT-1")
        assert response.status_code == 404
    
    async def test_multiple_concurrent_requests(self, mock_youtrack_base_url, mock_api_token):
        """Test multiple concurrent requests."""
        async with YouTrackClient(mock_youtrack_base_url, mock_api_token) as client:
            import asyncio
            
            # Make multiple concurrent requests
            tasks = [
                client.get_issue_full("TEST-1"),
                client.get_issue_full("TEST-2"),
                client.list_projects()
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert results[0].id == "TEST-1"
            assert results[1].id == "TEST-2" 
            assert len(results[2]) == 1  # Projects


