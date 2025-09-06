"""Test fixtures and configuration for integration tests."""

import asyncio
import pytest
import threading
import time
from typing import AsyncGenerator
import uvicorn
import httpx
from .mock_server import MockYouTrackServer


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Global reference to mock server instance
_mock_server_instance = None


@pytest.fixture(scope="function")
async def mock_youtrack_server() -> AsyncGenerator[str, None]:
    """Start mock YouTrack server for testing."""
    global _mock_server_instance
    
    _mock_server_instance = MockYouTrackServer()
    
    # Start server in background thread
    def run_server():
        config = uvicorn.Config(
            _mock_server_instance.app,
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


@pytest.fixture(autouse=True)
def reset_mock_server_data():
    """Reset mock server data before each test."""
    import httpx
    
    # Reset server data via HTTP endpoint (server is running in separate thread)
    try:
        with httpx.Client() as client:
            response = client.post("http://127.0.0.1:8089/reset", timeout=5.0)
            print(f"[pytest fixture] Called /reset, status: {response.status_code}")
            if response.status_code == 200:
                # Wait a bit for reset to complete
                time.sleep(0.1)
    except Exception as e:
        print(f"[pytest fixture] Exception during reset: {e}")
        pass
    
    yield
    
    # Also reset after test to ensure clean state
    try:
        with httpx.Client() as client:
            response = client.post("http://127.0.0.1:8089/reset", timeout=5.0)
            print(f"[pytest fixture] Called /reset after test, status: {response.status_code}")
    except Exception as e:
        print(f"[pytest fixture] Exception during post-test reset: {e}")
        pass
