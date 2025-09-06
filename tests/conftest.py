"""Pytest configuration and fixtures for MCP YouTrack tests."""

import pytest
import asyncio
import threading
import time
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
import uvicorn


# Import mock server if available for integration tests
try:
    from .mock_server import MockYouTrackServer
    MOCK_SERVER_AVAILABLE = True
except ImportError:
    MOCK_SERVER_AVAILABLE = False


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def mock_youtrack_server() -> AsyncGenerator[str, None]:
    """Start mock YouTrack server for testing."""
    if not MOCK_SERVER_AVAILABLE:
        pytest.skip("Mock server not available")
    
    mock_server = MockYouTrackServer()
    
    # Start server in background thread
    def run_server():
        config = uvicorn.Config(
            mock_server.app,
            host="127.0.0.1",
            port=8089,
            log_level="error"  # Reduce noise in tests
        )
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    yield "http://127.0.0.1:8089"
    
    # Cleanup happens automatically when thread is daemon


@pytest.fixture
def mock_youtrack_base_url(mock_youtrack_server) -> str:
    """Get mock YouTrack server base URL."""
    return mock_youtrack_server


@pytest.fixture
def mock_api_token() -> str:
    """Mock API token for testing."""
    return "mock-api-token-for-testing"


@pytest.fixture
def mock_youtrack_response():
    """Mock YouTrack API response."""
    return {
        "id": "PROJ-123",
        "summary": "Test Issue",
        "description": "This is a test issue",
        "state": {"name": "Open"},
        "priority": {"name": "Normal"},
        "assignee": {"name": "testuser"},
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_issue_full():
    """Mock complete issue data including comments and attachments."""
    return {
        "id": "PROJ-123",
        "summary": "Test Issue",
        "description": "This is a test issue",
        "state": {"name": "Open"},
        "priority": {"name": "Normal"},
        "assignee": {"name": "testuser"},
        "created": "2024-01-01T00:00:00Z",
        "updated": "2024-01-01T00:00:00Z",
        "comments": [
            {
                "id": "comment_1",
                "text": "First comment",
                "author": {"login": "user1"},
                "created": "2024-01-01T01:00:00Z"
            }
        ],
        "attachments": [
            {
                "id": "att_1",
                "name": "screenshot.png",
                "size": 1024,
                "contentType": "image/png",
                "url": "/api/attachments/att_1",
                "created": "2024-01-01T02:00:00Z",
                "author": {"login": "user1"}
            }
        ],
        "timeTracking": {
            "workItems": [
                {
                    "id": "work_1",
                    "duration": 3600000,  # 1 hour in milliseconds
                    "description": "Development work",
                    "date": "2024-01-01T03:00:00Z",
                    "author": {"login": "user1"}
                }
            ]
        }
    }


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    client = AsyncMock(spec=AsyncClient)
    return client


@pytest.fixture
def youtrack_config():
    """Test YouTrack configuration."""
    return {
        "base_url": "https://youtrack.example.com",
        "api_token": "test_token_123",
        "timeout": 30.0
    }
