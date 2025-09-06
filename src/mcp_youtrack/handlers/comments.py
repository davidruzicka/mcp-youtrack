"""MCP handler for YouTrack comments operations."""

from typing import Dict, Any
from ..youtrack_client import YouTrackClient


class CommentsHandler:
    async def update_comment(self, params: Dict[str, Any]):
        """Update a comment on an issue."""
        issue_id = params["issue_id"]
        comment_id = params["comment_id"]
        text = params["text"]
        return await self.youtrack_client.update_comment(issue_id, comment_id, text)
    """Handler for YouTrack comments operations."""
    
    def __init__(self, youtrack_client: YouTrackClient):
        """Initialize comments handler.
        
        Args:
            youtrack_client: Configured YouTrack API client
        """
        self.youtrack_client = youtrack_client
    
    async def add_comment(self, params: Dict[str, Any]):
        """Add a comment to an issue."""
        # TODO: Implement comment addition
        raise NotImplementedError("Comment addition not yet implemented")
