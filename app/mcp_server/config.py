"""MCP server configuration (env-driven, optional — never breaks boot)."""
import os


class MCPSettings:
    def __init__(self) -> None:
        self.enabled = os.getenv("MCP_ENABLED", "true").lower() == "true"
        self.server_name = os.getenv("MCP_SERVER_NAME", "devlog-mcp")
        self.server_version = os.getenv("MCP_SERVER_VERSION", "4.1.0")
        self.protocol_version = os.getenv("MCP_PROTOCOL_VERSION", "2024-11-05")
        self.path = os.getenv("MCP_PATH", "/mcp")
        # Comma-separated origins allowed to POST to /mcp (browsers). Empty = allow all.
        raw = os.getenv("MCP_ALLOWED_ORIGINS", "")
        self.allowed_origins = [o.strip() for o in raw.split(",") if o.strip()]
        self.rate_limit = os.getenv("MCP_RATE_LIMIT", "30/minute")
        # External AI clients authenticate the same way as REST: Bearer JWT.
        self.require_auth = os.getenv("MCP_REQUIRE_AUTH", "true").lower() == "true"


_settings: MCPSettings | None = None


def get_mcp_settings() -> MCPSettings:
    global _settings
    if _settings is None:
        _settings = MCPSettings()
    return _settings


def reset_mcp_settings() -> None:  # tests only
    global _settings
    _settings = None
