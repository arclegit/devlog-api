from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CodingSession, User
from app.schemas import SessionCreate, SessionUpdate, SessionResponse


router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/", response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_session = CodingSession(
        user_id=current_user.id,
        project_name=session_data.project_name,
        language=session_data.language,
        started_at=session_data.started_at,
        ended_at=session_data.ended_at,
        description=session_data.description,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session

@router.get("/", response_model=list[SessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(CodingSession)
        .filter(CodingSession.user_id == current_user.id)
        .all()
    )

    return sessions

@router.get("/{session_id}", response_model=SessionResponse)
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
        raise HTTPException(status_code=404, detail="Session not found")

    return session

@router.patch("/{session_id}", response_model=SessionResponse)
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
        raise HTTPException(status_code=404, detail="Session not found")

    update_data = session_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(session, field, value)

    db.commit()
    db.refresh(session)

    return session

@router.delete("/{session_id}")
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
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}