"""Configuration utilities for MCP YouTrack server."""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration class for MCP YouTrack server."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        
        # YouTrack configuration
        self.youtrack_url = os.getenv("YOUTRACK_URL", "https://davidruzicka.youtrack.cloud:443/api")
        self.youtrack_api_token = os.getenv("YOUTRACK_API_TOKEN")
        
        # MCP transport configuration
        self.mcp_transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
        self.mcp_host = os.getenv("MCP_HOST", "localhost")
        self.mcp_port = int(os.getenv("MCP_PORT", "8000"))
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required configuration is present."""
        if not self.youtrack_api_token:
            raise ValueError(
                "YOUTRACK_API_TOKEN environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        if self.mcp_transport not in ["stdio", "http"]:
            raise ValueError(f"Invalid MCP_TRANSPORT: {self.mcp_transport}. Must be 'stdio' or 'http'.")
    
    @property
    def is_http_transport(self) -> bool:
        """Check if HTTP transport is enabled."""
        return self.mcp_transport == "http"
    
    @property
    def is_stdio_transport(self) -> bool:
        """Check if STDIO transport is enabled."""
        return self.mcp_transport == "stdio"
    
    def get_youtrack_headers(self, additional_headers: Optional[dict] = None) -> dict:
        """Get headers for YouTrack API requests."""
        headers = {
            "Authorization": f"Bearer {self.youtrack_api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return (
            f"Config("
            f"youtrack_url={self.youtrack_url}, "
            f"mcp_transport={self.mcp_transport}, "
            f"mcp_host={self.mcp_host}, "
            f"mcp_port={self.mcp_port}"
            f")"
        )
