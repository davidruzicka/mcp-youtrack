"""HTTP streaming transport for MCP YouTrack server."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .server import MCPServer
from .utils.config import Config


logger = logging.getLogger(__name__)


class MCPHTTPServer:
    """HTTP streaming transport for MCP server."""
    
    def __init__(self, mcp_server: MCPServer, config: Config):
        """Initialize HTTP server.
        
        Args:
            mcp_server: Configured MCP server instance
            config: Server configuration
        """
        self.mcp_server = mcp_server
        self.config = config
        self.app = FastAPI(
            title="MCP YouTrack Server",
            description="Model Context Protocol server for YouTrack integration",
            version="0.1.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server info."""
            return {
                "name": "MCP YouTrack Server",
                "version": "0.1.0",
                "transport": "HTTP Streaming",
                "youtrack_url": self.config.youtrack_url
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy"}
        
        @self.app.post("/mcp/tools")
        async def list_tools():
            """List available MCP tools."""
            try:
                # Get tools from MCP server
                tools = await self.mcp_server.server._list_tools_handler()
                return {"tools": tools}
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/mcp/call")
        async def call_tool(request: Request):
            """Call an MCP tool."""
            try:
                body = await request.json()
                tool_name = body.get("name")
                arguments = body.get("arguments", {})
                
                if not tool_name:
                    raise HTTPException(status_code=400, detail="Tool name is required")
                
                # Call the tool
                result = await self.mcp_server.server._call_tool_handler(tool_name, arguments)
                return {"result": result}
                
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp/stream")
        async def stream_mcp():
            """Stream MCP server events using Server-Sent Events."""
            
            async def event_stream():
                """Generate server-sent events."""
                try:
                    # Send initial connection event
                    yield f"data: {json.dumps({'type': 'connected', 'message': 'MCP YouTrack Server connected'})}\n\n"
                    
                    # Keep the connection open until the client disconnects
                    # The connection will be kept alive by the server's keep-alive settings
                    while True:
                        await asyncio.sleep(3600)  # Just to keep the coroutine alive
                        
                except asyncio.CancelledError:
                    logger.info("SSE connection cancelled")
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
    
    async def start(self):
        """Start the HTTP server."""
        config = uvicorn.Config(
            self.app,
            host=self.config.mcp_host,
            port=self.config.mcp_port,
            log_level=self.config.log_level.lower(),
            timeout_keep_alive=self.config.http_keep_alive_timeout,
            timeout_graceful_shutdown=min(10, self.config.http_keep_alive_timeout // 2)  # Graceful shutdown timeout
        )
        
        server = uvicorn.Server(config)
        logger.info(f"Starting HTTP server on {self.config.mcp_host}:{self.config.mcp_port}")
        
        # Run server in background
        await server.serve()
    
    async def stop(self):
        """Stop the HTTP server."""
        logger.info("Stopping HTTP server")


def create_http_server(config: Config, youtrack_client) -> MCPHTTPServer:
    """Create and configure HTTP server.
    
    Args:
        config: Server configuration
        youtrack_client: Configured YouTrack client
        
    Returns:
        Configured HTTP server instance
    """
    mcp_server = MCPServer(youtrack_client)
    return MCPHTTPServer(mcp_server, config)


async def run_http_server(config: Config, youtrack_client):
    """Run HTTP server with given configuration.
    
    Args:
        config: Server configuration
        youtrack_client: Configured YouTrack client
    """
    server = create_http_server(config, youtrack_client)
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await server.stop()
