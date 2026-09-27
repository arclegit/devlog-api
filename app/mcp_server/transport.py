"""Streamable-HTTP transport: POST /mcp (+ GET discovery)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.mcp_server.auth import authenticate_mcp_token
from app.mcp_server.config import get_mcp_settings
from app.mcp_server.server import AUTH_ERROR, PARSE_ERROR, rpc_error
from app.rate_limit import limiter

router = APIRouter(tags=["MCP"])
PUBLIC_METHODS = {"initialize", "tools/list", "ping",
                  "notifications/initialized", "notifications/cancelled"}


def _cors(request: Request) -> dict:
    s = get_mcp_settings()
    o = request.headers.get("origin", "*")
    if s.allowed_origins and o not in s.allowed_origins and "*" not in s.allowed_origins:
        o = s.allowed_origins[0]
    return {"Access-Control-Allow-Origin": o,
        "Access-Control-Allow-Headers": "Authorization, Content-Type, Mcp-Session-Id",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS"}


@router.options("/mcp")
async def mcp_preflight(request: Request):
    return JSONResponse({}, headers=_cors(request))


@router.get("/mcp")
async def mcp_discovery(request: Request):
    s = get_mcp_settings()
    from app.mcp_server.registry import TOOLS
    from app.mcp_server.server import server_info
    return JSONResponse({
        "server": server_info(), "protocolVersion": s.protocol_version,
        "transport": "streamable-http", "endpoint": s.path,
        "auth": {"type": "bearer_jwt", "header": "Authorization",
                 "how": "Login via POST /auth/login, then send Authorization: Bearer <token>"},
        "tools": [{"name": n, "description": t["description"]} for n, t in TOOLS.items()],
    }, headers=_cors(request))


@router.post("/mcp")
@limiter.limit("30/minute")
async def mcp_endpoint(request: Request, db: Session = Depends(get_db)):
    from app.mcp_server.server import dispatch
    s = get_mcp_settings()
    if not s.enabled:
        return JSONResponse({"error": {"code": "503", "message": "MCP server disabled."}},
                            status_code=503, headers=_cors(request))
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(rpc_error(None, PARSE_ERROR, "Parse error: body must be JSON."),
                            headers=_cors(request))
    if not isinstance(body, dict):
        return JSONResponse(rpc_error(None, PARSE_ERROR, "body must be a JSON object."),
                            headers=_cors(request))
    user_id = None
    auth_h = request.headers.get("authorization")
    needs = body.get("method") == "tools/call" or (s.require_auth and body.get("method") not in PUBLIC_METHODS)
    if needs:
        try:
            user_id = authenticate_mcp_token(auth_h, db).id
        except Exception as exc:
            from fastapi import HTTPException as FH
            st = exc.status_code if isinstance(exc, FH) else 401
            return JSONResponse(rpc_error(body.get("id"), AUTH_ERROR, getattr(exc, "detail", "Unauthorized")),
                                status_code=st, headers=_cors(request))
    elif auth_h:
        try:
            user_id = authenticate_mcp_token(auth_h, db).id
        except Exception:
            user_id = None
    payload, st = dispatch(body, user_id, db)
    if payload is None:
        return JSONResponse({}, status_code=202, headers=_cors(request))
    return JSONResponse(payload, status_code=st, headers=_cors(request))
