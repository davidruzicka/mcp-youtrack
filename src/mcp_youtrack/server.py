"""MCP server implementation for YouTrack."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import Tool

from .youtrack_client import YouTrackClient
from .handlers import IssuesHandler, CommentsHandler, WorkHandler, ProjectsHandler


class MCPServer:
    """Model Context Protocol server for YouTrack integration."""
    
    def __init__(self, youtrack_client: YouTrackClient):
        """Initialize MCP server with YouTrack client.
        
        Args:
            youtrack_client: Configured YouTrack API client
        """
        self.youtrack_client = youtrack_client
        self.server = Server("youtrack")
        
        # Initialize handlers
        self.issues_handler = IssuesHandler(youtrack_client)
        self.comments_handler = CommentsHandler(youtrack_client)
        self.work_handler = WorkHandler(youtrack_client)
        self.projects_handler = ProjectsHandler(youtrack_client)
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all MCP tools."""
        
        # Issues tools
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="youtrack.get_issue",
                    description="Get complete issue data including comments, attachments, and work items",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue_id": {
                                "type": "string",
                                "description": "ID of the issue to retrieve"
                            },
                            "include_comments": {
                                "type": "boolean",
                                "description": "Whether to include comments",
                                "default": True
                            },
                            "include_attachments": {
                                "type": "boolean",
                                "description": "Whether to include attachments",
                                "default": True
                            },
                            "include_work_items": {
                                "type": "boolean",
                                "description": "Whether to include work items",
                                "default": True
                            }
                        },
                        "required": ["issue_id"]
                    }
                ),
                Tool(
                    name="youtrack.list_issues",
                    description="List issues with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project": {
                                "type": "string",
                                "description": "Project key to filter by"
                            },
                            "state": {
                                "type": "string",
                                "description": "State to filter by"
                            },
                            "assignee": {
                                "type": "string",
                                "description": "Assignee to filter by"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of issues to return",
                                "default": 50
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Number of issues to skip",
                                "default": 0
                            }
                        }
                    }
                ),
                Tool(
                    name="youtrack.download_attachment",
                    description="Download attachment content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue_id": {
                                "type": "string",
                                "description": "ID of the issue"
                            },
                            "attachment_id": {
                                "type": "string",
                                "description": "ID of the attachment"
                            }
                        },
                        "required": ["issue_id", "attachment_id"]
                    }
                ),
                Tool(
                    name="youtrack.upload_attachment",
                    description="Upload a new attachment to an issue",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "issue_id": {
                                "type": "string",
                                "description": "ID of the issue"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Name of the file"
                            },
                            "content": {
                                "type": "string",
                                "description": "File content as base64 encoded string"
                            }
                        },
                        "required": ["issue_id", "filename", "content"]
                    }
                )
            ]
        
        # Tool implementations
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            """Handle tool calls."""
            
            if name == "youtrack.get_issue":
                result = await self.issues_handler.get_issue(arguments)
                # Convert dataclass to dict for JSON serialization
                return self._serialize_issue(result)
                
            elif name == "youtrack.list_issues":
                result = await self.issues_handler.list_issues(arguments)
                return {"issues": result}
                
            elif name == "youtrack.download_attachment":
                # TODO: Implement attachment download
                raise NotImplementedError("Attachment download not yet implemented")
                
            elif name == "youtrack.upload_attachment":
                # TODO: Implement attachment upload
                raise NotImplementedError("Attachment upload not yet implemented")
                
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    def _serialize_issue(self, issue) -> Dict[str, Any]:
        """Serialize issue dataclass to dict for JSON response."""
        return {
            "id": issue.id,
            "summary": issue.summary,
            "description": issue.description,
            "state": issue.state,
            "priority": issue.priority,
            "assignee": issue.assignee,
            "created": issue.created.isoformat(),
            "updated": issue.updated.isoformat(),
            "comments": [
                {
                    "id": c.id,
                    "text": c.text,
                    "author": c.author,
                    "created": c.created.isoformat(),
                    "updated": c.updated.isoformat() if c.updated else None
                }
                for c in issue.comments
            ],
            "attachments": [
                {
                    "id": a.id,
                    "name": a.name,
                    "size": a.size,
                    "content_type": a.content_type,
                    "url": a.url,
                    "created": a.created.isoformat(),
                    "author": a.author
                }
                for a in issue.attachments
            ],
            "work_items": [
                {
                    "id": w.id,
                    "duration": w.duration,
                    "description": w.description,
                    "date": w.date.isoformat(),
                    "author": w.author,
                    "type": w.type
                }
                for w in issue.work_items
            ],
            "custom_fields": issue.custom_fields,
            "project": issue.project,
            "reporter": issue.reporter,
            "tags": issue.tags
        }
        
    async def start(self):
        """Start the MCP server."""
        # TODO: Implement server startup
        pass
        
    async def stop(self):
        """Stop the MCP server."""
        # TODO: Implement server shutdown
        pass
        
    async def run_stdio(self):
        """Run the server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="youtrack",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )
