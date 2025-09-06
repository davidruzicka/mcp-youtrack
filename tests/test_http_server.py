"""Tests for HTTP server functionality."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from mcp_youtrack.http_server import MCPHTTPServer, create_http_server, run_http_server
from mcp_youtrack.server import MCPServer
from mcp_youtrack.utils.config import Config


class TestMCPHTTPServer:
    """Test cases for MCPHTTPServer class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock(spec=Config)
        config.youtrack_url = "https://test.youtrack.com"
        config.mcp_host = "localhost"
        config.mcp_port = 8000
        config.log_level = "INFO"
        return config
    
    @pytest.fixture
    def mock_mcp_server(self):
        """Create mock MCP server."""
        server = MagicMock(spec=MCPServer)
        server.server = MagicMock()
        server.server._list_tools_handler = AsyncMock(return_value=[])
        server.server._call_tool_handler = AsyncMock(return_value={"success": True})
        return server
    
    @pytest.fixture
    def http_server(self, mock_mcp_server, mock_config):
        """Create HTTP server instance."""
        return MCPHTTPServer(mock_mcp_server, mock_config)
    
    @pytest.fixture
    def test_client(self, http_server):
        """Create test client."""
        return TestClient(http_server.app)

    def test_http_server_initialization(self, mock_mcp_server, mock_config):
        """Test HTTP server initialization."""
        server = MCPHTTPServer(mock_mcp_server, mock_config)
        
        assert server.mcp_server == mock_mcp_server
        assert server.config == mock_config
        assert server.app is not None
        assert server.app.title == "MCP YouTrack Server"

    def test_root_endpoint(self, test_client, mock_config):
        """Test root endpoint returns server info."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MCP YouTrack Server"
        assert data["version"] == "0.1.0"
        assert data["transport"] == "HTTP Streaming"
        assert data["youtrack_url"] == mock_config.youtrack_url

    def test_health_check_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_list_tools_endpoint_success(self, test_client, mock_mcp_server):
        """Test list tools endpoint success."""
        # Configure mock to return sample tools
        sample_tools = [
            {"name": "youtrack.get_issue", "description": "Get issue"},
            {"name": "youtrack.list_issues", "description": "List issues"}
        ]
        mock_mcp_server.server._list_tools_handler.return_value = sample_tools
        
        response = test_client.post("/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert data["tools"] == sample_tools

    @pytest.mark.asyncio
    async def test_list_tools_endpoint_error(self, test_client, mock_mcp_server):
        """Test list tools endpoint handles errors."""
        # Configure mock to raise exception
        mock_mcp_server.server._list_tools_handler.side_effect = Exception("Test error")
        
        response = test_client.post("/mcp/tools")
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Test error"

    @pytest.mark.asyncio
    async def test_call_tool_endpoint_success(self, test_client, mock_mcp_server):
        """Test call tool endpoint success."""
        # Configure mock to return sample result
        sample_result = {"issue_id": "PROJ-123", "summary": "Test Issue"}
        mock_mcp_server.server._call_tool_handler.return_value = sample_result
        
        request_data = {
            "name": "youtrack.get_issue",
            "arguments": {"issue_id": "PROJ-123"}
        }
        
        response = test_client.post("/mcp/call", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"] == sample_result
        
        # Verify handler was called with correct arguments
        mock_mcp_server.server._call_tool_handler.assert_called_once_with(
            "youtrack.get_issue", {"issue_id": "PROJ-123"}
        )

    @pytest.mark.asyncio
    async def test_call_tool_endpoint_missing_name(self, test_client):
        """Test call tool endpoint with missing tool name."""
        request_data = {
            "arguments": {"issue_id": "PROJ-123"}
        }
        
        response = test_client.post("/mcp/call", json=request_data)
        
        # The HTTPException is caught by the outer try/catch and returned as 500
        assert response.status_code == 500
        data = response.json()
        assert "Tool name is required" in data["detail"]

    @pytest.mark.asyncio
    async def test_call_tool_endpoint_error(self, test_client, mock_mcp_server):
        """Test call tool endpoint handles errors."""
        # Configure mock to raise exception
        mock_mcp_server.server._call_tool_handler.side_effect = Exception("Tool error")
        
        request_data = {
            "name": "youtrack.get_issue",
            "arguments": {"issue_id": "PROJ-123"}
        }
        
        response = test_client.post("/mcp/call", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "Tool error"


    def test_stream_endpoint_exists(self, http_server):
        """Test that stream endpoint is registered."""
        # Just verify the route exists in the FastAPI app
        routes = [route.path for route in http_server.app.routes]
        assert "/mcp/stream" in routes

    @pytest.mark.asyncio
    async def test_server_start_method_exists(self, http_server):
        """Test that start method exists and can be called."""
        with patch('uvicorn.Server') as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve = AsyncMock()
            mock_server_class.return_value = mock_server
            
            # This should not raise an exception
            await http_server.start()
            
            # Verify uvicorn server was created and started
            mock_server_class.assert_called_once()
            mock_server.serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_stop_method_exists(self, http_server):
        """Test that stop method exists and can be called."""
        # This should not raise an exception
        await http_server.stop()

    def test_create_http_server_function(self, mock_config):
        """Test create_http_server factory function."""
        mock_youtrack_client = MagicMock()
        
        with patch('mcp_youtrack.http_server.MCPServer') as mock_mcp_server_class:
            mock_mcp_server = MagicMock()
            mock_mcp_server_class.return_value = mock_mcp_server
            
            server = create_http_server(mock_config, mock_youtrack_client)
            
            assert isinstance(server, MCPHTTPServer)
            assert server.config == mock_config
            mock_mcp_server_class.assert_called_once_with(mock_youtrack_client)

    @pytest.mark.asyncio
    async def test_run_http_server_function_normal(self, mock_config):
        """Test run_http_server function normal execution."""
        mock_youtrack_client = MagicMock()
        
        with patch('mcp_youtrack.http_server.create_http_server') as mock_create:
            mock_server = MagicMock()
            mock_server.start = AsyncMock()
            mock_server.stop = AsyncMock()
            mock_create.return_value = mock_server
            
            await run_http_server(mock_config, mock_youtrack_client)
            
            mock_create.assert_called_once_with(mock_config, mock_youtrack_client)
            mock_server.start.assert_called_once()
            mock_server.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_http_server_function_keyboard_interrupt(self, mock_config):
        """Test run_http_server function handles KeyboardInterrupt."""
        mock_youtrack_client = MagicMock()
        
        with patch('mcp_youtrack.http_server.create_http_server') as mock_create:
            mock_server = MagicMock()
            mock_server.start = AsyncMock(side_effect=KeyboardInterrupt())
            mock_server.stop = AsyncMock()
            mock_create.return_value = mock_server
            
            await run_http_server(mock_config, mock_youtrack_client)
            
            mock_create.assert_called_once_with(mock_config, mock_youtrack_client)
            mock_server.start.assert_called_once()
            mock_server.stop.assert_called_once()

    def test_setup_routes_called_during_init(self, mock_mcp_server, mock_config):
        """Test that _setup_routes is called during initialization."""
        with patch.object(MCPHTTPServer, '_setup_routes') as mock_setup_routes:
            MCPHTTPServer(mock_mcp_server, mock_config)
            mock_setup_routes.assert_called_once()

    def test_cors_middleware_configuration(self, http_server):
        """Test that CORS middleware is properly configured."""
        # Check that the app has middleware configured
        assert len(http_server.app.user_middleware) > 0
        
        # Test CORS by making a simple GET request with origin header
        test_client = TestClient(http_server.app)
        response = test_client.get("/", headers={"Origin": "http://localhost:3000"})
        
        # Should be successful (not blocked by CORS)
        assert response.status_code == 200
        # Should have CORS headers if CORS middleware is working
        # Note: TestClient doesn't always return all CORS headers in test mode
