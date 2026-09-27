"""DevLog MCP package (v4.1.0).

Zero third-party dependencies: implements JSON-RPC 2.0 + MCP handshake
over Streamable HTTP by hand, so no `mcp` PyPI package is required.
"""
from app.mcp_server.config import MCPSettings, get_mcp_settings

__all__ = ["MCPSettings", "get_mcp_settings"]
