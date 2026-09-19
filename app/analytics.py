from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Float, cast, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CodingSession, User
from app.schemas import (
    AnalyticsSummaryResponse,
    DailyAnalyticsResponse,
    LanguageAnalyticsResponse,
    ProjectAnalyticsResponse,
    WeeklyAnalyticsResponse,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


def analytics_filters(user_id: int, from_: datetime | None, to: datetime | None):
    if from_ is not None and to is not None and from_ > to:
        raise HTTPException(status_code=422, detail="from must be earlier than or equal to to")
    filters = [CodingSession.user_id == user_id, CodingSession.ended_at.is_not(None)]
    if from_ is not None:
        filters.append(CodingSession.started_at >= from_)
    if to is not None:
        filters.append(CodingSession.started_at <= to)
    return filters


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get activity summary",
    description=(
        "Return the total number of completed coding sessions, "
        "total coding time, and average completed session duration "
        "for the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_analytics_summary(
    from_: datetime | None = Query(None, alias="from", description="Include sessions starting at or after this ISO 8601 timestamp."),
    to: datetime | None = Query(None, description="Include sessions starting at or before this ISO 8601 timestamp."),
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
        .filter(*analytics_filters(current_user.id, from_, to))
        .one()
    )

    total_sessions, total_coding_seconds, average_session_seconds = result

    return AnalyticsSummaryResponse(
        total_sessions=total_sessions,
        total_coding_seconds=total_coding_seconds,
        average_session_seconds=average_session_seconds,
    )


@router.get(
    "/languages",
    response_model=list[LanguageAnalyticsResponse],
    summary="Get activity by language",
    description=(
        "Return completed coding activity grouped by programming language "
        "for the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_language_analytics(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
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
        .filter(*analytics_filters(current_user.id, from_, to))
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


@router.get(
    "/projects",
    response_model=list[ProjectAnalyticsResponse],
    summary="Get activity by project",
    description=(
        "Return completed coding activity grouped by project "
        "for the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_project_analytics(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
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
        .filter(*analytics_filters(current_user.id, from_, to))
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


@router.get(
    "/daily",
    response_model=list[DailyAnalyticsResponse],
    summary="Get daily activity",
    description=(
        "Return completed coding activity grouped by the day "
        "of the session start time for the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_daily_analytics(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
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
        local_started_at = CodingSession.started_at.op("AT TIME ZONE")(current_user.timezone)
        date_group = func.date_trunc(
            "day",
            local_started_at,
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
        .filter(*analytics_filters(current_user.id, from_, to))
        .group_by(date_group)
        .order_by(date_group.asc())
        .all()
    )

    return [
        DailyAnalyticsResponse(
            date=(
                date_value.strftime("%Y-%m-%d")
                if hasattr(date_value, "strftime")
                else str(date_value)
            ),
            total_sessions=total_sessions,
            total_coding_seconds=total_coding_seconds,
        )
        for date_value, total_sessions, total_coding_seconds in results
    ]


@router.get(
    "/weekly",
    response_model=list[WeeklyAnalyticsResponse],
    summary="Get weekly activity",
    description=(
        "Return completed coding activity grouped by week "
        "for the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_weekly_analytics(
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
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
        local_started_at = CodingSession.started_at.op("AT TIME ZONE")(current_user.timezone)
        week_group = func.date_trunc(
            "week",
            local_started_at,
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
        .filter(*analytics_filters(current_user.id, from_, to))
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
