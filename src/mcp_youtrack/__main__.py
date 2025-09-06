"""Main entry point for MCP YouTrack server."""

import asyncio
import logging
import sys
from pathlib import Path

from .utils.config import Config
from .youtrack_client import YouTrackClient
from .server import MCPServer
from .http_server import run_http_server


def setup_logging(config: Config):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=config.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main():
    """Main entry point."""
    try:
        # Load configuration
        config = Config()
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting MCP YouTrack Server")
        logger.info(f"Configuration: {config}")
        
        # Create YouTrack client
        youtrack_client = YouTrackClient(
            base_url=config.youtrack_url,
            api_token=config.youtrack_api_token,
            timeout=30.0
        )
        
        # Test YouTrack connection
        logger.info("Testing YouTrack connection...")
        try:
            # Try to list projects to test connection
            projects = await youtrack_client.list_projects()
            logger.info(f"Successfully connected to YouTrack. Found {len(projects)} projects.")
        except Exception as e:
            logger.error(f"Failed to connect to YouTrack: {e}")
            logger.error("Please check your YOUTRACK_URL and YOUTRACK_API_TOKEN configuration.")
            sys.exit(1)
        
        # Start appropriate transport
        if config.is_http_transport:
            logger.info("Starting HTTP transport...")
            await run_http_server(config, youtrack_client)
        else:
            logger.info("Starting STDIO transport...")
            mcp_server = MCPServer(youtrack_client)
            await mcp_server.run_stdio()
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if 'youtrack_client' in locals():
            await youtrack_client.close()


if __name__ == "__main__":
    asyncio.run(main())
