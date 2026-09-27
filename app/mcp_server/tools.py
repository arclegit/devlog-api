"""DevLog MCP tools part 1: list/analytics/breakdown (own DB sessions)."""
from datetime import datetime

from app.models import CodingSession, User


def tool_list_sessions(user_id: int, limit: int = 10, project=None, db=None) -> dict:
    from app.database import SessionLocal as _SL
    limit = max(1, min(int(limit or 10), 50))
    _own = db is None
    db = db or _SL()
    try:
        query = db.query(CodingSession).filter(
            CodingSession.user_id == user_id
        ).order_by(CodingSession.started_at.desc())
        if project:
            query = query.filter(CodingSession.project_name == project)
        rows = query.limit(limit).all()
        return {"sessions": [
            {"id": s.id, "project_name": s.project_name, "language": s.language,
             "started_at": s.started_at.isoformat() if s.started_at else None,
             "ended_at": s.ended_at.isoformat() if s.ended_at else None,
             "description": s.description, "active": s.ended_at is None}
            for s in rows]}
    finally:
        if _own:
            db.close()


def tool_analytics_summary(user_id: int, from_=None, to=None, db=None) -> dict:
    from app.database import SessionLocal as _SL
    _own = db is None
    db = db or _SL()
    try:
        user = db.get(User, user_id)
        from app.analytics import get_analytics_summary
        result = get_analytics_summary(
            from_=datetime.fromisoformat(from_) if from_ else None,
            to=datetime.fromisoformat(to) if to else None,
            db=db, current_user=user)
        return result.model_dump()
    finally:
        if _own:
            db.close()


def tool_activity_breakdown(user_id: int, from_=None, to=None, db=None) -> dict:
    from app.database import SessionLocal as _SL
    _own = db is None
    db = db or _SL()
    try:
        user = db.get(User, user_id)
        from app.analytics import get_daily_analytics, get_language_analytics, get_project_analytics
        from_dt = datetime.fromisoformat(from_) if from_ else None
        to_dt = datetime.fromisoformat(to) if to else None
        return {
            "languages": [r.model_dump() for r in get_language_analytics(from_=from_dt, to=to_dt, db=db, current_user=user)],
            "projects": [r.model_dump() for r in get_project_analytics(from_=from_dt, to=to_dt, db=db, current_user=user)],
            "daily": [r.model_dump() for r in get_daily_analytics(from_=from_dt, to=to_dt, db=db, current_user=user)],
        }
    finally:
        if _own:
            db.close()
