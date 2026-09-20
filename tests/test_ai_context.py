from datetime import datetime, timezone

from app.ai.context import build_activity_context
from app.models import CodingSession, User


def test_build_activity_context(db):
    user = User(
        email="ai-context@example.com",
        password_hash="test-hash",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        CodingSession(
            user_id=user.id,
            project_name="DevLog API",
            language="Python",
            started_at=datetime(
                2026,
                9,
                10,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            ended_at=datetime(
                2026,
                9,
                10,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            description="AI work",
        )
    )

    db.commit()

    context = build_activity_context(
        db=db,
        current_user=user,
        start_date=datetime(2026, 9, 1).date(),
        end_date=datetime(2026, 9, 30).date(),
    )

    assert context.total_sessions == 1
    assert context.total_coding_seconds > 0
    assert context.languages[0]["language"] == "Python"
    assert context.projects[0]["project_name"] == "DevLog API"