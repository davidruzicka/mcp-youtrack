"""Tests for configuration utilities."""

import pytest
import os
from unittest.mock import patch, mock_open
from pathlib import Path

from mcp_youtrack.utils.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        return {
            "YOUTRACK_URL": "https://test.youtrack.cloud",
            "YOUTRACK_API_TOKEN": "test_token_123",
            "MCP_TRANSPORT": "http",
            "MCP_HOST": "0.0.0.0",
            "MCP_PORT": "9000",
            "LOG_LEVEL": "DEBUG"
        }
    
    def test_config_initialization_with_env_vars(self, mock_env_vars):
        """Test configuration initialization from environment variables."""
        with patch.dict(os.environ, mock_env_vars):
            config = Config()
            
            assert config.youtrack_url == "https://test.youtrack.cloud"
            assert config.youtrack_api_token == "test_token_123"
            assert config.mcp_transport == "http"
            assert config.mcp_host == "0.0.0.0"
            assert config.mcp_port == 9000
            assert config.log_level == "DEBUG"
    
    def test_config_defaults(self):
        """Test configuration defaults when environment variables are not set."""
        # Test with minimal required configuration
        with patch.dict(os.environ, {
            "YOUTRACK_API_TOKEN": "test_token",
            "MCP_PORT": "8000",
            "MCP_TRANSPORT": "stdio"
        }, clear=True):
            config = Config()
            
            # Check defaults
            assert config.youtrack_url == "https://davidruzicka.youtrack.cloud:443/api"
            assert config.mcp_host == "localhost"
            assert config.log_level == "INFO"
    
    def test_config_validation_missing_token(self):
        """Test that configuration validation fails without API token."""
        with patch.dict(os.environ, {"YOUTRACK_API_TOKEN": ""}, clear=True):
            with pytest.raises(ValueError, match="YOUTRACK_API_TOKEN environment variable is required"):
                Config()
    
    def test_config_validation_invalid_transport(self):
        """Test that configuration validation fails with invalid transport."""
        with patch.dict(os.environ, {
            "YOUTRACK_API_TOKEN": "test_token",
            "MCP_TRANSPORT": "invalid"
        }):
            with pytest.raises(ValueError, match="Invalid MCP_TRANSPORT: invalid"):
                Config()
    
    def test_config_properties(self, mock_env_vars):
        """Test configuration properties."""
        with patch.dict(os.environ, mock_env_vars):
            config = Config()
            
            assert config.is_http_transport is True
            assert config.is_stdio_transport is False
    
    def test_config_stdio_transport(self):
        """Test stdio transport configuration."""
        with patch.dict(os.environ, {
            "YOUTRACK_API_TOKEN": "test_token",
            "MCP_TRANSPORT": "stdio"
        }):
            config = Config()
            
            assert config.is_stdio_transport is True
            assert config.is_http_transport is False
    
    def test_get_youtrack_headers(self, mock_env_vars):
        """Test YouTrack headers generation."""
        with patch.dict(os.environ, mock_env_vars):
            config = Config()
            
            headers = config.get_youtrack_headers()
            
            assert headers["Authorization"] == "Bearer test_token_123"
            assert headers["Content-Type"] == "application/json"
            assert headers["Accept"] == "application/json"
    
    def test_get_youtrack_headers_with_additional(self, mock_env_vars):
        """Test YouTrack headers with additional headers."""
        with patch.dict(os.environ, mock_env_vars):
            config = Config()
            
            additional_headers = {"X-Custom-Header": "custom_value"}
            headers = config.get_youtrack_headers(additional_headers)
            
            assert headers["Authorization"] == "Bearer test_token_123"
            assert headers["X-Custom-Header"] == "custom_value"
    
    def test_config_repr(self, mock_env_vars):
        """Test configuration string representation."""
        with patch.dict(os.environ, mock_env_vars):
            config = Config()
            
            repr_str = repr(config)
            
            assert "Config(" in repr_str
            assert "youtrack_url=https://test.youtrack.cloud" in repr_str
            assert "mcp_transport=http" in repr_str
            assert "mcp_host=0.0.0.0" in repr_str
            assert "mcp_port=9000" in repr_str
    
    @patch('pathlib.Path.exists')
    @patch('dotenv.load_dotenv')
    def test_dotenv_loading(self, mock_load_dotenv, mock_exists):
        """Test that .env file is loaded when it exists."""
        mock_exists.return_value = True
        
        with patch.dict(os.environ, {"YOUTRACK_API_TOKEN": "test_token"}):
            # Clear any existing .env loading
            with patch('mcp_youtrack.utils.config.load_dotenv', mock_load_dotenv):
                Config()
                
                mock_load_dotenv.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('dotenv.load_dotenv')
    def test_dotenv_not_loaded_when_missing(self, mock_load_dotenv, mock_exists):
        """Test that .env file is not loaded when it doesn't exist."""
        mock_exists.return_value = False
        
        with patch.dict(os.environ, {"YOUTRACK_API_TOKEN": "test_token"}):
            Config()
            
            mock_load_dotenv.assert_not_called()
    
    def test_port_parsing(self):
        """Test that port is properly parsed as integer."""
        with patch.dict(os.environ, {
            "YOUTRACK_API_TOKEN": "test_token",
            "MCP_PORT": "12345"
        }):
            config = Config()
            
            assert config.mcp_port == 12345
            assert isinstance(config.mcp_port, int)
    
    def test_port_parsing_invalid(self):
        """Test that invalid port raises error."""
        with patch.dict(os.environ, {
            "YOUTRACK_API_TOKEN": "test_token",
            "MCP_PORT": "invalid_port"
        }):
            with pytest.raises(ValueError):
                Config()
