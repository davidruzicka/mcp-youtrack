"""MCP handler for YouTrack projects operations."""

from typing import Dict, Any
from ..youtrack_client import YouTrackClient


class ProjectsHandler:
    """Handler for YouTrack projects operations."""
    
    def __init__(self, youtrack_client: YouTrackClient):
        """Initialize projects handler.
        
        Args:
            youtrack_client: Configured YouTrack API client
        """
        self.youtrack_client = youtrack_client
    
    async def list_projects(self, params: Dict[str, Any]):
        """List all projects."""
        # TODO: Implement project listing
        raise NotImplementedError("Project listing not yet implemented")
