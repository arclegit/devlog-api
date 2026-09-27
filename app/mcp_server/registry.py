"""DevLog MCP tools part 2: RAG search + AI summary + registry."""
from datetime import date

from app.models import User


def tool_search_notes(user_id: int, query: str, top_k: int = 5, db=None) -> dict:
    from app.database import SessionLocal as _SL
    top_k = max(1, min(int(top_k or 5), 10))
    _own = db is None
    db = db or _SL()
    try:
        from app.rag.factory import create_embedding_provider
        from app.rag.service import RAGService
        try:
            results = RAGService(provider=create_embedding_provider()).retrieve_chunks(
                db=db, user_id=user_id, query=query, top_k=top_k)
        except Exception as exc:
            return {"results": [], "warning": f"retrieval unavailable: {exc}"}
        return {"results": [
            {"chunk_id": r["chunk_id"], "document_id": r["document_id"],
             "title": r.get("title"), "content": r["content"][:800],
             "score": r.get("score", 0.0)} for r in results]}
    finally:
        if _own:
            db.close()


def tool_activity_summary(user_id: int, start_date: str, end_date: str, db=None) -> dict:
    from app.database import SessionLocal as _SL
    _own = db is None
    db = db or _SL()
    try:
        from app.ai.factory import create_ai_provider
        from app.ai.service import AIService
        user = db.get(User, user_id)
        response = AIService(provider=create_ai_provider()).generate_activity_summary(
            db=db, current_user=user,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date))
        return response.model_dump()
    finally:
        if _own:
            db.close()


def _h_list(user_id: int, args: dict, db=None) -> dict:
    from app.mcp_server.tools import tool_list_sessions
    return tool_list_sessions(user_id, limit=args.get("limit", 10), project=args.get("project"), db=db)


def _h_sum(user_id: int, args: dict, db=None) -> dict:
    from app.mcp_server.tools import tool_analytics_summary
    return tool_analytics_summary(user_id, from_=args.get("from"), to=args.get("to"), db=db)


def _h_break(user_id: int, args: dict, db=None) -> dict:
    from app.mcp_server.tools import tool_activity_breakdown
    return tool_activity_breakdown(user_id, from_=args.get("from"), to=args.get("to"), db=db)


TOOLS: dict = {
    "list_sessions": {
        "description": "List the authenticated user's recent coding sessions (newest first).",
        "inputSchema": {"type": "object", "properties": {
            "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
            "project": {"type": "string"}}},
        "handler": _h_list},
    "analytics_summary": {
        "description": "Totals and averages for completed sessions. Optional ISO-8601 from/to.",
        "inputSchema": {"type": "object", "properties": {
            "from": {"type": "string"}, "to": {"type": "string"}}},
        "handler": _h_sum},
    "activity_breakdown": {
        "description": "Grouped analytics by language, project, and day.",
        "inputSchema": {"type": "object", "properties": {
            "from": {"type": "string"}, "to": {"type": "string"}}},
        "handler": _h_break},
    "search_notes": {
        "description": "Hybrid semantic+keyword search over the user's DevLog notes/documents.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10}},
            "required": ["query"]},
        "handler": lambda uid, a, db=None: tool_search_notes(uid, query=a.get("query", ""), top_k=a.get("top_k", 5), db=db)},
    "activity_summary": {
        "description": "AI-generated interpretation of activity for a date range (YYYY-MM-DD).",
        "inputSchema": {"type": "object", "properties": {
            "start_date": {"type": "string"}, "end_date": {"type": "string"}},
            "required": ["start_date", "end_date"]},
        "handler": lambda uid, a, db=None: tool_activity_summary(uid, start_date=a["start_date"], end_date=a["end_date"], db=db)},
}
