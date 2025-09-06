"""Tests for YouTrack issues handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from mcp_youtrack.handlers.issues import IssuesHandler
from mcp_youtrack.models import IssueFull, Comment, Attachment, WorkItem


class TestIssuesHandler:
    """Test cases for IssuesHandler class."""
    
    @pytest.fixture
    def mock_youtrack_client(self):
        """Create a mock YouTrack client."""
        client = MagicMock()
        client.get_issue_full = AsyncMock()
        return client
    
    @pytest.fixture
    def issues_handler(self, mock_youtrack_client):
        """Create an issues handler with mock client."""
        return IssuesHandler(mock_youtrack_client)
    
    @pytest.fixture
    def mock_issue_full(self):
        """Create mock issue data."""
        return IssueFull(
            id="PROJ-123",
            summary="Test Issue",
            description="This is a test issue",
            state="Open",
            priority="Normal",
            assignee="testuser",
            created=datetime(2024, 1, 1, 0, 0, 0),
            updated=datetime(2024, 1, 1, 0, 0, 0),
            comments=[
                Comment(
                    id="comment_1",
                    text="First comment",
                    author="user1",
                    created=datetime(2024, 1, 1, 1, 0, 0)
                )
            ],
            attachments=[
                Attachment(
                    id="att_1",
                    name="screenshot.png",
                    size=1024,
                    content_type="image/png",
                    url="/api/attachments/att_1",
                    created=datetime(2024, 1, 1, 2, 0, 0),
                    author="user1"
                )
            ],
            work_items=[
                WorkItem(
                    id="work_1",
                    duration=3600000,  # 1 hour in milliseconds
                    description="Development work",
                    date=datetime(2024, 1, 1, 3, 0, 0),
                    author="user1"
                )
            ],
            custom_fields={},
            project="PROJ",
            reporter="user1",
            tags=["bug", "frontend"]
        )
    
    @pytest.mark.asyncio
    async def test_get_issue_success(self, issues_handler, mock_youtrack_client, mock_issue_full):
        """Test successful retrieval of issue."""
        # Arrange
        params = {
            "issue_id": "PROJ-123",
            "include_comments": True,
            "include_attachments": True,
            "include_work_items": True
        }
        mock_youtrack_client.get_issue_full.return_value = mock_issue_full
        
        # Act
        result = await issues_handler.get_issue(params)
        
        # Assert
        assert result.id == "PROJ-123"
        assert result.summary == "Test Issue"
        assert len(result.comments) == 1
        assert len(result.attachments) == 1
        assert len(result.work_items) == 1
        mock_youtrack_client.get_issue_full.assert_called_once_with("PROJ-123")
    
    @pytest.mark.asyncio
    async def test_get_issue_with_defaults(self, issues_handler, mock_youtrack_client, mock_issue_full):
        """Test issue retrieval with default parameters."""
        # Arrange
        params = {"issue_id": "PROJ-123"}
        mock_youtrack_client.get_issue_full.return_value = mock_issue_full
        
        # Act
        result = await issues_handler.get_issue(params)
        
        # Assert
        assert result.id == "PROJ-123"
        mock_youtrack_client.get_issue_full.assert_called_once_with("PROJ-123")
    
    @pytest.mark.asyncio
    async def test_list_issues_empty(self, issues_handler):
        """Test listing issues returns empty list for now."""
        # Arrange
        params = {"project": "PROJ", "limit": 10}
        
        # Act
        result = await issues_handler.list_issues(params)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_create_issue_not_implemented(self, issues_handler):
        """Test that issue creation raises NotImplementedError."""
        # Arrange
        params = {
            "project": "PROJ",
            "summary": "New Issue",
            "description": "Description"
        }
        
        # Act & Assert
        with pytest.raises(NotImplementedError, match="Issue creation not yet implemented"):
            await issues_handler.create_issue(params)
    
    
    @pytest.mark.asyncio
    async def test_break_down_story_not_implemented(self, issues_handler):
        """Test that story breakdown raises NotImplementedError."""
        # Arrange
        params = {
            "story_id": "PROJ-123",
            "tasks": [
                {"summary": "Task 1", "description": "First task"},
                {"summary": "Task 2", "description": "Second task"}
            ]
        }
        
        # Act & Assert
        with pytest.raises(NotImplementedError, match="Story breakdown not yet implemented"):
            await issues_handler.break_down_story(params)
    
    @pytest.mark.asyncio
    async def test_update_issue(self, issues_handler, mock_youtrack_client, mock_issue_full):
        # Arrange
        mock_youtrack_client.update_issue = AsyncMock()
        mock_youtrack_client.get_issue_full = AsyncMock(return_value=mock_issue_full)
        params = {
            "issue_id": "PROJ-123",
            "summary": "Updated summary",
            "description": "Updated description",
            "state": "In Progress",
            "priority": "Critical",
            "assignee": "user2",
            "tags": ["backend", "urgent"]
        }
        # Act
        result = await issues_handler.update_issue(params)
        # Assert
        mock_youtrack_client.update_issue.assert_awaited_once()
        mock_youtrack_client.get_issue_full.assert_awaited_once_with("PROJ-123")
        assert result == mock_issue_full
