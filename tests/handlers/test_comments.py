"""Tests for YouTrack comments handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from mcp_youtrack.handlers.comments import CommentsHandler
from mcp_youtrack.models import Comment

class TestCommentsHandler:
    @pytest.fixture
    def mock_youtrack_client(self):
        client = MagicMock()
        client.update_comment = AsyncMock()
        return client

    @pytest.fixture
    def comments_handler(self, mock_youtrack_client):
        return CommentsHandler(mock_youtrack_client)

    @pytest.mark.asyncio
    async def test_update_comment(self, comments_handler, mock_youtrack_client):
        mock_comment = Comment(
            id="c1",
            text="Updated text",
            author="user1",
            created=datetime(2024, 1, 1, 0, 0, 0),
            updated=datetime(2024, 1, 2, 0, 0, 0)
        )
        mock_youtrack_client.update_comment.return_value = mock_comment
        params = {"issue_id": "PROJ-1", "comment_id": "c1", "text": "Updated text"}
        result = await comments_handler.update_comment(params)
        assert result == mock_comment
        mock_youtrack_client.update_comment.assert_awaited_once_with("PROJ-1", "c1", "Updated text")
