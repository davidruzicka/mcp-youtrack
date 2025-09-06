"""MCP server for JetBrains YouTrack.

This package provides a Model Context Protocol (MCP) server implementation
for interacting with JetBrains YouTrack instances.
"""

__version__ = "0.1.0"
__author__ = "David Ruzicka"

from .server import MCPServer

__all__ = ["MCPServer"]
