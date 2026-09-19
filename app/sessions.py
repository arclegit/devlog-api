from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CodingSession, User
from app.schemas import SessionCreate, SessionResponse, SessionUpdate


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


@router.post(
    "/",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a coding session",
    description=(
        "Create a coding session for the authenticated user. "
        "The session owner is determined from the authenticated JWT, "
        "not from a client-provided user ID."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
        409: {
            "description": "The user already has an active coding session."
        },
    },
)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only active sessions are subject to the one-active-session rule.
    if session_data.ended_at is None:
        active_session = (
            db.query(CodingSession)
            .filter(
                CodingSession.user_id == current_user.id,
                CodingSession.ended_at.is_(None),
            )
            .first()
        )

        if active_session is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has an active coding session",
            )

    new_session = CodingSession(
        user_id=current_user.id,
        project_name=session_data.project_name,
        language=session_data.language,
        started_at=session_data.started_at,
        ended_at=session_data.ended_at,
        description=session_data.description,
    )

    db.add(new_session)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active coding session",
        )

    db.refresh(new_session)

    return new_session


@router.post(
    "/{session_id}/end",
    response_model=SessionResponse,
    summary="End a coding session",
    description=(
        "End an active coding session owned by the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
        404: {
            "description": "The requested coding session was not found."
        },
        409: {
            "description": "The coding session is already ended."
        },
    },
)
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(CodingSession)
        .filter(
            CodingSession.id == session_id,
            CodingSession.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.ended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already ended",
        )

    session.ended_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)

    return session


@router.get(
    "/",
    response_model=list[SessionResponse],
    summary="List coding sessions",
    description=(
        "Return coding sessions belonging to the authenticated user. "
        "Results can be paginated using skip and limit."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_sessions(
    skip: int = Query(
        0,
        ge=0,
        description="Number of sessions to skip before returning results.",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
        description=(
            "Maximum number of sessions to return. "
            "Must be between 1 and 100."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(CodingSession)
        .filter(CodingSession.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return sessions


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get a coding session",
    description=(
        "Return a coding session owned by the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
        404: {
            "description": "The requested coding session was not found."
        },
    },
)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(CodingSession)
        .filter(
            CodingSession.id == session_id,
            CodingSession.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return session


@router.patch(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Update a coding session",
    description=(
        "Update one or more fields of a coding session owned by "
        "the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
        404: {
            "description": "The requested coding session was not found."
        },
        409: {
            "description": "The update would violate the session lifecycle rules."
        },
        422: {
            "description": (
                "Validation failed, including when ended_at is earlier "
                "than started_at."
            )
        },
    },
)
def update_session(
    session_id: int,
    session_data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(CodingSession)
        .filter(
            CodingSession.id == session_id,
            CodingSession.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    update_data = session_data.model_dump(exclude_unset=True)

    # A completed session cannot be reopened.
    if (
        session.ended_at is not None
        and "ended_at" in update_data
        and update_data["ended_at"] is None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed sessions cannot be reopened",
        )

    # Build the final state of the session before applying changes.
    new_started_at = update_data.get(
        "started_at",
        session.started_at,
    )

    new_ended_at = update_data.get(
        "ended_at",
        session.ended_at,
    )

    # Validate the relationship between started_at and ended_at.
    if new_ended_at is not None and new_ended_at <= new_started_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ended_at must be greater than started_at",
        )

    # If the update would turn this session into an active session,
    # make sure the user does not already have another active session.
    if (
        new_ended_at is None
        and session.ended_at is not None
    ):
        active_session = (
            db.query(CodingSession)
            .filter(
                CodingSession.user_id == current_user.id,
                CodingSession.ended_at.is_(None),
                CodingSession.id != session.id,
            )
            .first()
        )

        if active_session is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has an active coding session",
            )

    # Apply the validated changes.
    for field, value in update_data.items():
        setattr(session, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active coding session",
        )

    db.refresh(session)

    return session


@router.delete(
    "/{session_id}",
    summary="Delete a coding session",
    description=(
        "Delete a coding session owned by the authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
        404: {
            "description": "The requested coding session was not found."
        },
    },
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = (
        db.query(CodingSession)
        .filter(
            CodingSession.id == session_id,
            CodingSession.user_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}
