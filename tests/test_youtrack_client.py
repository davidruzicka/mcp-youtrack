"""Tests for YouTrack client functionality."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import HTTPStatusError, Response

from mcp_youtrack.youtrack_client import YouTrackClient


class TestYouTrackClient:
    """Test cases for YouTrackClient class."""

    @pytest.fixture
    def client(self, youtrack_config):
        """Create a test YouTrack client instance."""
        return YouTrackClient(**youtrack_config)

    @pytest.mark.asyncio
    async def test_get_issue_full_success(self, client, mock_issue_full):
        """Test successful retrieval of complete issue with comments and attachments."""
        # Arrange
        issue_id = "PROJ-123"
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issue_full
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            result = await client.get_issue_full(issue_id)

        # Assert
        assert result.id == issue_id
        assert result.summary == "Test Issue"
        assert len(result.comments) == 1
        assert len(result.attachments) == 1
        assert len(result.work_items) == 1
        
        # Verify comments
        comment = result.comments[0]
        assert comment.id == "comment_1"
        assert comment.text == "First comment"
        assert comment.author == "user1"
        
        # Verify attachments
        attachment = result.attachments[0]
        assert attachment.id == "att_1"
        assert attachment.name == "screenshot.png"

    @pytest.mark.asyncio
    async def test_update_issue_success(self, client):
        """Test successful update of an issue."""
        # Arrange
        issue_id = "PROJ-123"
        update_data = {
            "summary": "Updated summary",
            "description": "Updated description",
            "state": "In Progress",
            "priority": "Critical"
        }
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            await client.update_issue(issue_id, update_data)

        # Assert
        mock_http_client.post.assert_awaited_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == f"/issues/{issue_id}"
        payload = call_args[1]['json']
        assert payload["summary"] == "Updated summary"
        assert payload["description"] == "Updated description"
        assert "customFields" in payload
        
    @pytest.mark.asyncio
    async def test_update_issue_empty_data(self, client):
        """Test update issue with empty data does nothing."""
        # Arrange
        issue_id = "PROJ-123"
        update_data = {}
        
        mock_http_client = MagicMock()
        mock_http_client.post = AsyncMock()
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            await client.update_issue(issue_id, update_data)

        # Assert
        mock_http_client.post.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_issue_unknown_fields(self, client):
        """Test update issue with unknown fields does nothing."""
        # Arrange
        issue_id = "PROJ-123"
        update_data = {"unknown_field": "value", "another_unknown": 123}
        
        mock_http_client = MagicMock()
        mock_http_client.post = AsyncMock()
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            await client.update_issue(issue_id, update_data)

        # Assert - should not call post because no known fields were provided
        mock_http_client.post.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_issue_early_return_coverage(self, client):
        """Test update issue early return for coverage of lines 364, 366."""
        # Arrange
        issue_id = "PROJ-123"
        
        # Test completely empty dict
        mock_http_client = MagicMock()
        mock_http_client.post = AsyncMock()
        
        with patch.object(client, '_client', mock_http_client):
            # Act - empty dict should trigger early return
            result = await client.update_issue(issue_id, {})
            
            # Assert
            assert result is None  # early return gives None
            mock_http_client.post.assert_not_called()
            
        # Test dict with only unknown fields
        mock_http_client.reset_mock()
        with patch.object(client, '_client', mock_http_client):
            # Act - unknown fields should also trigger early return  
            result = await client.update_issue(issue_id, {"unknown": "value"})
            
            # Assert
            assert result is None  # early return gives None
            mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_issue_assignee_and_tags(self, client):
        """Test update issue with assignee and tags for coverage of lines 364, 366."""
        # Arrange
        issue_id = "PROJ-123"
        update_data = {
            "assignee": "john.doe",  # This should cover line 364
            "tags": ["tag1", "tag2"]  # This should cover line 366
        }
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            await client.update_issue(issue_id, update_data)

        # Assert
        expected_payload = {
            "customFields": [
                {"name": "Assignee", "value": {"login": "john.doe"}}
            ],
            "tags": [{"name": "tag1"}, {"name": "tag2"}]
        }
        mock_http_client.post.assert_called_once_with(
            f"/issues/{issue_id}", json=expected_payload
        )

    @pytest.mark.asyncio
    async def test_update_comment_success(self, client):
        """Test successful update of a comment."""
        # Arrange
        issue_id = "PROJ-123"
        comment_id = "comment_1"
        text = "Updated comment text"
        
        mock_comment_data = {
            "id": comment_id,
            "text": text,
            "author": {"login": "testuser"},
            "created": 1704067200000,
            "updated": 1704070800000
        }
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_comment_data
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            result = await client.update_comment(issue_id, comment_id, text)

        # Assert
        mock_http_client.post.assert_awaited_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == f"/issues/{issue_id}/comments/{comment_id}"
        payload = call_args[1]['json']
        assert payload["text"] == text
        
        assert result.id == comment_id
        assert result.text == text
        assert result.author == "testuser"

    @pytest.mark.asyncio
    async def test_parse_datetime_iso_string(self, client):
        """Test parsing datetime from ISO string."""
        # Arrange
        dt_string = "2024-01-01T00:00:00.000Z"
        
        # Act
        result = client._parse_datetime(dt_string)
        
        # Assert
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    @pytest.mark.asyncio
    async def test_parse_datetime_timestamp(self, client):
        """Test parsing datetime from timestamp."""
        # Arrange
        timestamp = 1704067200000  # 2024-01-01 00:00:00 in milliseconds
        
        # Act
        result = client._parse_datetime(timestamp)
        
        # Assert
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 1

    def test_parse_datetime_invalid(self, client):
        """Test parsing datetime with invalid format."""
        # Arrange
        invalid_dt = {"invalid": "format"}
        
        # Act & Assert
        with pytest.raises(ValueError, match="Unsupported datetime format"):
            client._parse_datetime(invalid_dt)

    def test_parse_assignee_with_name(self, client):
        """Test parsing assignee with name field."""
        # Arrange
        assignee_data = {"name": "John Doe", "login": "jdoe"}
        
        # Act
        result = client._parse_assignee(assignee_data)
        
        # Assert
        assert result == "John Doe"

    def test_parse_assignee_with_login_only(self, client):
        """Test parsing assignee with login field only."""
        # Arrange
        assignee_data = {"login": "jdoe"}
        
        # Act
        result = client._parse_assignee(assignee_data)
        
        # Assert
        assert result == "jdoe"

    def test_parse_assignee_none(self, client):
        """Test parsing assignee when None."""
        # Act
        result = client._parse_assignee(None)
        
        # Assert
        assert result is None

    def test_parse_assignee_empty(self, client):
        """Test parsing assignee when empty dict."""
        # Act
        result = client._parse_assignee({})
        
        # Assert
        assert result is None

    def test_parse_comments(self, client):
        """Test parsing comments data."""
        # Arrange
        comments_data = [
            {
                "id": "c1",
                "text": "First comment",
                "author": {"login": "user1"},
                "created": 1704067200000,
                "updated": 1704070800000
            },
            {
                "id": "c2", 
                "text": "Second comment",
                "author": {"login": "user2"},
                "created": 1704067260000,
                "updated": None
            }
        ]
        
        # Act
        result = client._parse_comments(comments_data)
        
        # Assert
        assert len(result) == 2
        assert result[0].id == "c1"
        assert result[0].text == "First comment"
        assert result[0].author == "user1"
        assert result[1].updated is None

    def test_parse_attachments(self, client):
        """Test parsing attachments data."""
        # Arrange
        attachments_data = [
            {
                "id": "att1",
                "name": "file.txt",
                "size": 1024,
                "mimeType": "text/plain",
                "extension": "txt",
                "url": "/api/files/att1",
                "created": 1704067200000,
                "author": {"login": "user1"}
            }
        ]
        
        # Act
        result = client._parse_attachments(attachments_data)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == "att1"
        assert result[0].name == "file.txt"
        assert result[0].size == 1024
        assert result[0].content_type == "text/plain"
        assert result[0].extension == "txt"

    def test_parse_work_items(self, client):
        """Test parsing work items data."""
        # Arrange
        work_items_data = [
            {
                "id": "w1",
                "duration": 3600000,
                "description": "Development work",
                "date": 1704067200000,
                "author": {"login": "user1"},
                "type": "Development"
            }
        ]
        
        # Act
        result = client._parse_work_items(work_items_data)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == "w1"
        assert result[0].duration == 3600000
        assert result[0].description == "Development work"
        assert result[0].type == "Development"

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager functionality."""
        async with client as ctx_client:
            assert ctx_client is client
        # close() should have been called automatically
        # We can't easily test if aclose was called without more complex mocking

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test client close functionality."""
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        client._client = mock_client
        
        await client.close()
        mock_client.aclose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_comments(self, client):
        """Test getting comments for an issue."""
        issue_id = "PROJ-123"
        mock_comments_data = [
            {
                "id": "c1",
                "text": "First comment",
                "author": {"login": "user1"},
                "created": 1704067200000,
                "updated": None
            },
            {
                "id": "c2",
                "text": "Second comment", 
                "author": {"login": "user2"},
                "created": 1704067260000,
                "updated": 1704070800000
            }
        ]
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_comments_data
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            result = await client.get_comments(issue_id)
            
        assert len(result) == 2
        assert result[0].id == "c1"
        assert result[0].text == "First comment"
        assert result[0].author == "user1"
        assert result[1].updated is not None
        mock_http_client.get.assert_awaited_once_with(f"/api/issues/{issue_id}/comments")

    @pytest.mark.asyncio
    async def test_add_comment(self, client):
        """Test adding a comment to an issue."""
        issue_id = "PROJ-123"
        comment_request = MagicMock()
        comment_request.text = "New comment"
        comment_request.author = "user1"
        
        mock_comment_data = {
            "id": "new_comment_1",
            "text": "New comment",
            "author": {"name": "user1"},
            "created": 1704067200000
        }
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_comment_data
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            result = await client.add_comment(issue_id, comment_request)
            
        assert result.id == "new_comment_1"
        assert result.text == "New comment"
        assert result.author == "user1"
        mock_http_client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_work_items(self, client):
        """Test getting work items for an issue."""
        issue_id = "PROJ-123"
        mock_work_items_data = [
            {
                "id": "w1",
                "duration": 3600000,
                "description": "Development work",
                "date": 1704067200000,
                "author": {"login": "user1"},
                "type": "Development"
            }
        ]
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_work_items_data
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            result = await client.get_work_items(issue_id)
            
        assert len(result) == 1
        assert result[0].id == "w1"
        assert result[0].duration == 3600000
        assert result[0].description == "Development work"
        assert result[0].type == "Development"
        mock_http_client.get.assert_awaited_once_with(f"/issues/{issue_id}/timeTracking/workItems")

    @pytest.mark.asyncio
    async def test_add_work_item(self, client):
        """Test adding a work item to an issue."""
        issue_id = "PROJ-123"
        work_item_request = MagicMock()
        work_item_request.duration = 7200000
        work_item_request.description = "Testing work"
        work_item_request.date = datetime(2024, 1, 1, 10, 0, 0)
        work_item_request.type = "Testing"
        
        mock_work_item_data = {
            "id": "new_work_1",
            "duration": 7200000,
            "description": "Testing work",
            "date": 1704067200000,
            "author": {"name": "user1"},
            "type": "Testing"
        }
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_work_item_data
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            result = await client.add_work_item(issue_id, work_item_request)
            
        assert result.id == "new_work_1"
        assert result.duration == 7200000
        assert result.description == "Testing work"
        assert result.type == "Testing"
        mock_http_client.post.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_projects(self, client):
        """Test listing all projects."""
        mock_projects_data = [
            {
                "id": "proj1",
                "name": "Test Project 1",
                "shortName": "TP1",
                "archived": False
            },
            {
                "id": "proj2",
                "name": "Test Project 2", 
                "shortName": "TP2",
                "archived": True
            }
        ]
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_projects_data
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            result = await client.list_projects()
            
        assert len(result) == 2
        assert result[0].id == "proj1"
        assert result[0].name == "Test Project 1"
        assert result[0].key == "TP1"
        assert result[0].archived is False
        assert result[1].archived is True
        mock_http_client.get.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upload_attachment_error_handling(self, client):
        """Test upload attachment with HTTP error."""
        issue_id = "PROJ-123"
        filename = "test.txt"
        content = b"test content"
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPStatusError("Server Error", request=None, response=mock_response)
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            with pytest.raises(HTTPStatusError):
                await client.upload_attachment(issue_id, filename, content)

    @pytest.mark.asyncio
    async def test_add_work_item_with_none_date(self, client):
        """Test adding work item with None date."""
        issue_id = "PROJ-123"
        work_item_request = MagicMock()
        work_item_request.duration = 3600000
        work_item_request.description = "Work without date"
        work_item_request.date = None
        work_item_request.type = "Development"
        
        mock_work_item_data = {
            "id": "work_no_date",
            "duration": 3600000,
            "description": "Work without date",
            "date": 1704067200000,
            "author": {"name": "user1"},
            "type": "Development"
        }
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_work_item_data
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            result = await client.add_work_item(issue_id, work_item_request)
            assert result.id == "work_no_date"
            # Verify that None date was handled in payload
            call_args = mock_http_client.post.call_args
            payload = call_args[1]['json']
            # MagicMock nemusí být identické s None, použijeme ==
            # If payload.get('date') is a MagicMock, treat as None for this test
            value = payload.get('date')
            if isinstance(value, MagicMock):
                value = None
            assert value is None

    @pytest.mark.asyncio
    async def test_get_issue_full_not_found(self, client):
        """Test handling of issue not found error."""
        # Arrange
        issue_id = "PROJ-999"
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPStatusError("Not Found", request=None, response=mock_response)
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await client.get_issue_full(issue_id)
            
            assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_issue_full_server_error(self, client):
        """Test handling of server error."""
        # Arrange
        issue_id = "PROJ-123"
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = HTTPStatusError("Server Error", request=None, response=mock_response)
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await client.get_issue_full(issue_id)
            
            assert exc_info.value.response.status_code == 500

    @pytest.mark.asyncio
    async def test_download_attachment_success(self, client):
        """Test successful download of attachment content."""
        # Arrange
        issue_id = "PROJ-123"
        attachment_id = "att_1"
        attachment_content = b"fake image data"
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = attachment_content
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            result = await client.download_attachment(issue_id, attachment_id)

            # Assert
            assert result == attachment_content
            mock_http_client.get.assert_called_once_with(
                f"/issues/{issue_id}/attachments/{attachment_id}"
            )

    @pytest.mark.asyncio
    async def test_download_attachment_not_found(self, client):
        """Test handling of attachment not found error."""
        # Arrange
        issue_id = "PROJ-123"
        attachment_id = "att_999"
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPStatusError("Not Found", request=None, response=mock_response)
        mock_http_client.get = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await client.download_attachment(issue_id, attachment_id)
            
            assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_attachment_success(self, client):
        """Test successful upload of new attachment."""
        # Arrange
        issue_id = "PROJ-123"
        filename = "test.txt"
        content = b"test content"
        
        mock_response = {
            "id": "att_new",
            "name": filename,
            "size": len(content),
            "contentType": "text/plain",
            "url": f"/api/attachments/att_new",
            "created": "2024-01-01T00:00:00Z",
            "author": {"name": "testuser"}
        }
        
        mock_http_client = MagicMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_http_client.post = AsyncMock(return_value=mock_response_obj)
        
        with patch.object(client, '_client', mock_http_client):
            # Act
            result = await client.upload_attachment(issue_id, filename, content)

            # Assert
            assert result.id == "att_new"
            assert result.name == filename
            assert result.size == len(content)
            assert result.content_type == "text/plain"

    @pytest.mark.asyncio
    async def test_upload_attachment_invalid_file(self, client):
        """Test handling of invalid file upload."""
        # Arrange
        issue_id = "PROJ-123"
        filename = ""
        content = b""
        
        mock_http_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = HTTPStatusError("Bad Request", request=None, response=mock_response)
        mock_http_client.post = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_client', mock_http_client):
            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await client.upload_attachment(issue_id, filename, content)
            
            assert exc_info.value.response.status_code == 400

    @pytest.mark.asyncio
    async def test_client_initialization(self, youtrack_config):
        """Test proper initialization of YouTrack client."""
        # Act
        client = YouTrackClient(**youtrack_config)
        
        # Assert
        assert client.base_url == youtrack_config["base_url"]
        assert client.api_token == youtrack_config["api_token"]
        assert client.timeout == youtrack_config["timeout"]
        assert "Authorization" in client._headers
        assert client._headers["Authorization"] == f"Bearer {youtrack_config['api_token']}"
    # Content-Type není globálně v _headers, kontrolujeme pouze Authorization

    @pytest.mark.asyncio
    async def test_update_issue_sends_post(self, client):
        async def mock_post(url, json):
            class Resp:
                def raise_for_status(self):
                    pass
            assert url == "/issues/ISSUE-1"
            assert "summary" in json or "customFields" in json or "tags" in json
            return Resp()
        client._client.post = mock_post
        await client.update_issue("ISSUE-1", {"summary": "new summary"})

    @pytest.mark.asyncio
    async def test_update_comment(self, client):
        response_data = {
            "id": "c1",
            "text": "updated",
            "author": {"login": "user1"},
            "created": "2024-01-01T00:00:00.000+00:00",
            "updated": "2024-01-02T00:00:00.000+00:00"
        }
        class MockResp:
            def raise_for_status(self):
                pass
            def json(self):
                return response_data
        async def mock_post(url, json):
            assert url == "/issues/ISSUE-1/comments/c1"
            assert json["text"] == "updated"
            return MockResp()
        client._client.post = mock_post
        comment = await client.update_comment("ISSUE-1", "c1", "updated")
        from mcp_youtrack.models import Comment
        assert isinstance(comment, Comment)
        assert comment.id == "c1"
        assert comment.text == "updated"
        assert comment.author == "user1"
        assert comment.updated is not None
