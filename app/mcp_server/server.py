"""Minimal JSON-RPC 2.0 + MCP dispatcher (no `mcp` package needed)."""
import structlog

from app.mcp_server.config import get_mcp_settings

log = structlog.get_logger()

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
AUTH_ERROR = -32000


def rpc_result(msg_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def rpc_error(msg_id, code: int, message: str, data=None) -> dict:
    err: dict = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": msg_id, "error": err}


def server_info() -> dict:
    s = get_mcp_settings()
    return {"name": s.server_name, "version": s.server_version}


def handle_initialize(msg_id, params: dict) -> dict:
    s = get_mcp_settings()
    return rpc_result(msg_id, {
        "protocolVersion": s.protocol_version,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": server_info()})


def handle_tools_list(msg_id) -> dict:
    from app.mcp_server.registry import TOOLS
    return rpc_result(msg_id, {"tools": [
        {"name": n, "description": t["description"], "inputSchema": t["inputSchema"]}
        for n, t in TOOLS.items()]})


def handle_tools_call(msg_id, params: dict, user_id: int, db=None) -> dict:
    from app.mcp_server.registry import TOOLS
    name = (params or {}).get("name")
    args = (params or {}).get("arguments") or {}
    if name not in TOOLS:
        return rpc_error(msg_id, METHOD_NOT_FOUND, f"Unknown tool: {name}")
    try:
        output = TOOLS[name]["handler"](user_id, args, db)
    except KeyError as exc:
        return rpc_error(msg_id, INVALID_PARAMS, f"Missing argument: {exc}")
    except ValueError as exc:
        return rpc_error(msg_id, INVALID_PARAMS, str(exc))
    except Exception as exc:  # never leak internals
        log.error("mcp_tool_failed", tool=name, error=str(exc))
        return rpc_error(msg_id, INTERNAL_ERROR, "Tool execution failed.")
    import json
    return rpc_result(msg_id, {
        "content": [{"type": "text", "text": json.dumps(output, default=str)}],
        "structuredContent": output, "isError": False})


def dispatch(body: dict, user_id: int | None, db=None):
    """Route one JSON-RPC message. Returns (payload, http_status)."""
    msg_id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}
    if body.get("jsonrpc") != "2.0" or not method:
        return rpc_error(msg_id, INVALID_REQUEST, "Invalid JSON-RPC 2.0 request."), 200
    if method == "initialize":
        return handle_initialize(msg_id, params), 200
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None, 202
    if method == "ping":
        return rpc_result(msg_id, {}), 200
    if method == "tools/list":
        return handle_tools_list(msg_id), 200
    if method == "tools/call":
        if user_id is None:
            return rpc_error(msg_id, AUTH_ERROR, "Unauthorized: Bearer token required."), 401
        return handle_tools_call(msg_id, params, user_id, db), 200
    return rpc_error(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}"), 200
