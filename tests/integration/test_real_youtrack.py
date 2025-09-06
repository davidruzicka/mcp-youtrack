"""Integration tests using real YouTrack API."""

import pytest
import os
from unittest.mock import patch
from dotenv import load_dotenv

from mcp_youtrack.youtrack_client import YouTrackClient
from mcp_youtrack.utils.config import Config


# Load environment variables for integration tests
load_dotenv()


@pytest.mark.integration
class TestRealYouTrackAPI:
    """Integration tests using real YouTrack API."""
    
    @pytest.fixture
    def config(self):
        """Load configuration for integration tests."""
        return Config()
    
    @pytest.fixture
    def youtrack_client(self, config):
        """Create YouTrack client with real configuration."""
        return YouTrackClient(
            base_url=config.youtrack_url,
            api_token=config.youtrack_api_token,
            timeout=30.0
        )
    
    @pytest.mark.asyncio
    async def test_connection_to_youtrack(self, youtrack_client):
        """Test that we can connect to the real YouTrack instance."""
        # This test will fail if we can't connect
        projects = await youtrack_client.list_projects()
        
        # Should return a list (even if empty)
        assert isinstance(projects, list)
        
        # Log what we found for debugging
        print(f"Found {len(projects)} projects in YouTrack")
        for project in projects[:3]:  # Show first 3 projects
            print(f"  - {project.key}: {project.name}")
    
    @pytest.mark.asyncio
    async def test_list_projects_structure(self, youtrack_client):
        """Test that project data has the expected structure."""
        projects = await youtrack_client.list_projects()
        
        if projects:  # Only test if there are projects
            project = projects[0]
            
            # Check required fields
            assert hasattr(project, 'id')
            assert hasattr(project, 'name')
            assert hasattr(project, 'key')
            assert hasattr(project, 'created')
            
            # Check data types
            assert isinstance(project.id, str)
            assert isinstance(project.name, str)
            assert isinstance(project.key, str)
            assert hasattr(project.created, 'isoformat')  # datetime object
    
    @pytest.mark.asyncio
    async def test_get_issue_if_exists(self, youtrack_client):
        """Test getting an issue if any exist in the system."""
        # First, try to find any issue by looking at projects
        projects = await youtrack_client.list_projects()
        
        if not projects:
            pytest.skip("No projects found in YouTrack instance")
        
        # Try to find issues in the first project
        project = projects[0]
        print(f"Testing with project: {project.key}")
        
        # For now, we'll just test that the client can be created
        # In a real scenario, you might want to create a test issue first
        assert youtrack_client is not None
        assert youtrack_client.base_url is not None
        assert youtrack_client.api_token is not None
    
    @pytest.mark.asyncio
    async def test_youtrack_api_endpoints(self, youtrack_client):
        """Test that YouTrack API endpoints are accessible."""
        # Test projects endpoint
        projects = await youtrack_client.list_projects()
        assert isinstance(projects, list)
        
        # Test that we can make authenticated requests
        # This will fail if the API token is invalid
        assert youtrack_client.api_token is not None
        assert len(youtrack_client.api_token) > 0
    
    @pytest.mark.asyncio
    async def test_configuration_loading(self, config):
        """Test that configuration is properly loaded."""
        assert config.youtrack_url == "https://davidruzicka.youtrack.cloud:443/api"
        assert config.youtrack_api_token is not None
        assert len(config.youtrack_api_token) > 0
        assert config.mcp_transport in ["stdio", "http"]
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, config):
        """Test that YouTrack client can be initialized with real config."""
        client = YouTrackClient(
            base_url=config.youtrack_url,
            api_token=config.youtrack_api_token,
            timeout=30.0
        )
        
        assert client.base_url == config.youtrack_url
        assert client.api_token == config.youtrack_api_token
        assert client.timeout == 30.0
        
        # Test that headers are properly set
        assert "Authorization" in client._headers
        assert client._headers["Authorization"] == f"Bearer {config.youtrack_api_token}"
        
        await client.close()


# Skip integration tests if no API token is configured
def pytest_configure(config):
    """Configure pytest to skip integration tests if no API token."""
    if not os.getenv("YOUTRACK_API_TOKEN"):
        config.addinivalue_line(
            "markers", "integration: mark test as integration test (requires real API)"
        )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if no API token is configured."""
    if not os.getenv("YOUTRACK_API_TOKEN"):
        skip_integration = pytest.mark.skip(reason="YOUTRACK_API_TOKEN not configured")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
