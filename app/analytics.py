from fastapi import APIRouter, Depends
from sqlalchemy import Float, cast, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CodingSession, User
from app.schemas import ( AnalyticsSummaryResponse, DailyAnalyticsResponse, LanguageAnalyticsResponse, ProjectAnalyticsResponse, WeeklyAnalyticsResponse, )


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.bind.dialect.name == "sqlite":
        duration = func.round(
            (
                func.julianday(CodingSession.ended_at)
                - func.julianday(CodingSession.started_at)
            )
            * 86400
        )
    else:
        duration = func.extract(
            "epoch",
            CodingSession.ended_at - CodingSession.started_at,
        )

    result = (
        db.query(
            func.count(CodingSession.id),
            cast(func.coalesce(func.sum(duration), 0), Float),
            cast(func.coalesce(func.avg(duration), 0), Float),
        )
        .filter(
            CodingSession.user_id == current_user.id,
            CodingSession.ended_at.is_not(None),
        )
        .one()
    )

    total_sessions, total_coding_seconds, average_session_seconds = result

    return AnalyticsSummaryResponse(
        total_sessions=total_sessions,
        total_coding_seconds=total_coding_seconds,
        average_session_seconds=average_session_seconds,
    )

@router.get("/languages", response_model=list[LanguageAnalyticsResponse])
def get_language_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.bind.dialect.name == "sqlite":
        duration = func.round(
            (
                func.julianday(CodingSession.ended_at)
                - func.julianday(CodingSession.started_at)
            )
            * 86400
        )
    else:
        duration = func.extract(
            "epoch",
            CodingSession.ended_at - CodingSession.started_at,
        )

    results = (
        db.query(
            CodingSession.language,
            func.count(CodingSession.id).label("total_sessions"),
            cast(func.sum(duration), Float).label("total_coding_seconds"),
        )
        .filter(
            CodingSession.user_id == current_user.id,
            CodingSession.ended_at.is_not(None),
        )
        .group_by(CodingSession.language)
        .order_by(func.sum(duration).desc())
        .all()
    )

    return [
        LanguageAnalyticsResponse(
            language=language,
            total_sessions=total_sessions,
            total_coding_seconds=total_coding_seconds,
        )
        for language, total_sessions, total_coding_seconds in results
    ]

@router.get("/projects", response_model=list[ProjectAnalyticsResponse])
def get_project_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.bind.dialect.name == "sqlite":
        duration = func.round(
            (
                func.julianday(CodingSession.ended_at)
                - func.julianday(CodingSession.started_at)
            )
            * 86400
        )
    else:
        duration = func.extract(
            "epoch",
            CodingSession.ended_at - CodingSession.started_at,
        )

    results = (
        db.query(
            CodingSession.project_name,
            func.count(CodingSession.id).label("total_sessions"),
            cast(func.sum(duration), Float).label("total_coding_seconds"),
        )
        .filter(
            CodingSession.user_id == current_user.id,
            CodingSession.ended_at.is_not(None),
        )
        .group_by(CodingSession.project_name)
        .order_by(func.sum(duration).desc())
        .all()
    )

    return [
        ProjectAnalyticsResponse(
            project_name=project_name,
            total_sessions=total_sessions,
            total_coding_seconds=total_coding_seconds,
        )
        for project_name, total_sessions, total_coding_seconds in results
    ]

@router.get("/daily", response_model=list[DailyAnalyticsResponse])
def get_daily_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.bind.dialect.name == "sqlite":
        date_group = func.date(CodingSession.started_at)

        duration = func.round(
            (
                func.julianday(CodingSession.ended_at)
                - func.julianday(CodingSession.started_at)
            )
            * 86400
        )
    else:
        date_group = func.date_trunc(
            "day",
            CodingSession.started_at,
        )

        duration = func.extract(
            "epoch",
            CodingSession.ended_at - CodingSession.started_at,
        )

    results = (
        db.query(
            date_group.label("date"),
            func.count(CodingSession.id).label("total_sessions"),
            cast(func.sum(duration), Float).label("total_coding_seconds"),
        )
        .filter(
            CodingSession.user_id == current_user.id,
            CodingSession.ended_at.is_not(None),
        )
        .group_by(date_group)
        .order_by(date_group.asc())
        .all()
    )

    return [
        DailyAnalyticsResponse(
            date=date_value.strftime("%Y-%m-%d")
            if hasattr(date_value, "strftime")
            else str(date_value),
            total_sessions=total_sessions,
            total_coding_seconds=total_coding_seconds,
        )
        for date_value, total_sessions, total_coding_seconds in results
    ]

@router.get("/weekly", response_model=list[WeeklyAnalyticsResponse])
def get_weekly_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.bind.dialect.name == "sqlite":
        week_group = func.strftime(
            "%Y-%W",
            CodingSession.started_at,
        )

        duration = func.round(
            (
                func.julianday(CodingSession.ended_at)
                - func.julianday(CodingSession.started_at)
            )
            * 86400
        )
    else:
        week_group = func.date_trunc(
            "week",
            CodingSession.started_at,
        )

        duration = func.extract(
            "epoch",
            CodingSession.ended_at - CodingSession.started_at,
        )

    results = (
        db.query(
            week_group.label("week"),
            func.count(CodingSession.id).label("total_sessions"),
            cast(func.sum(duration), Float).label("total_coding_seconds"),
        )
        .filter(
            CodingSession.user_id == current_user.id,
            CodingSession.ended_at.is_not(None),
        )
        .group_by(week_group)
        .order_by(week_group.asc())
        .all()
    )

    return [
        WeeklyAnalyticsResponse(
            week=(
                week_value.strftime("%Y-%m-%d")
                if hasattr(week_value, "strftime")
                else str(week_value)
            ),
            total_sessions=total_sessions,
            total_coding_seconds=total_coding_seconds,
        )
        for week_value, total_sessions, total_coding_seconds in results
    ]