"""v4.1.0 MCP tests: handshake, discovery, tools, auth isolation."""
from app.models import CodingSession, User
from app.security import create_access_token
from datetime import datetime, timezone


def _user(db, email="mcp@example.com"):
    u = User(email=email, password_hash="x", timezone="UTC")
    db.add(u); db.commit(); db.refresh(u)
    return u


def _rpc(client, method, params=None, token=None, raw=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = raw if raw is not None else {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    return client.post("/mcp", json=body, headers=headers)


def test_discovery(client):
    r = client.get("/mcp")
    assert r.status_code == 200
    assert r.json()["transport"] == "streamable-http"


def test_init_and_list(client, db):
    u = _user(db)
    t = create_access_token(u.id)
    r = _rpc(client, "initialize", {"protocolVersion": "2024-11-05"})
    assert r.json()["result"]["serverInfo"]["name"] == "devlog-mcp"
    r = _rpc(client, "tools/list", token=t)
    names = {x["name"] for x in r.json()["result"]["tools"]}
    assert {"list_sessions", "analytics_summary", "activity_breakdown", "search_notes", "activity_summary"} <= names


def test_call_needs_auth(client):
    r = _rpc(client, "tools/call", {"name": "list_sessions", "arguments": {}})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == -32000


def test_list_isolated(client, db):
    a = _user(db, "a@x.com"); b = _user(db, "b@x.com")
    now = datetime.now(timezone.utc)
    db.add(CodingSession(user_id=a.id, project_name="P", language="Python", started_at=now, description="n"))
    db.add(CodingSession(user_id=b.id, project_name="Q", language="Go", started_at=now, description="n"))
    db.commit()
    r = _rpc(client, "tools/call", {"name": "list_sessions", "arguments": {"limit": 5}}, token=create_access_token(a.id))
    import json
    out = json.loads(r.json()["result"]["content"][0]["text"])
    assert all(s["project_name"] == "P" for s in out["sessions"])


def test_unknown_tool_and_bad_json(client, db):
    u = _user(db, "u@x.com")
    r = _rpc(client, "tools/call", {"name": "nope", "arguments": {}}, token=create_access_token(u.id))
    assert r.json()["error"]["code"] == -32601
    r = client.post("/mcp", content=b"not json", headers={"Content-Type": "application/json"})
    assert r.json()["error"]["code"] == -32700
