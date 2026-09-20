from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from sqlalchemy.orm import Session

from app.models import User
from app.analytics import (
    get_analytics_summary,
    get_daily_analytics,
    get_language_analytics,
    get_project_analytics,
)

@dataclass
class ActivityContext:
    total_sessions: int
    total_coding_seconds: float
    average_session_seconds: float
    languages: list[dict]
    projects: list[dict]
    daily_activity: list[dict]

def build_activity_context(
    db: Session,
    current_user: User,
    start_date: date,
    end_date: date,
) -> ActivityContext:
    start_datetime = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )

    end_datetime = datetime.combine(
        end_date,
        time.max,
        tzinfo=timezone.utc,
    )

    summary = get_analytics_summary(
        from_=start_datetime,
        to=end_datetime,
        db=db,
        current_user=current_user,
    )

    languages = get_language_analytics(
        from_=start_datetime,
        to=end_datetime,
        db=db,
        current_user=current_user,
    )

    projects = get_project_analytics(
        from_=start_datetime,
        to=end_datetime,
        db=db,
        current_user=current_user,
    )

    daily_activity = get_daily_analytics(
        from_=start_datetime,
        to=end_datetime,
        db=db,
        current_user=current_user,
    )

    return ActivityContext(
        total_sessions=summary.total_sessions,
        total_coding_seconds=summary.total_coding_seconds,
        average_session_seconds=summary.average_session_seconds,
        languages=[
            item.model_dump()
            for item in languages
        ],
        projects=[
            item.model_dump()
            for item in projects
        ],
        daily_activity=[
            item.model_dump()
            for item in daily_activity
        ],
    )