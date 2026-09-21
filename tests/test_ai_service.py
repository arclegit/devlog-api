from datetime import date, datetime, timezone

from app.ai.mock_provider import MockAIProvider
from app.ai.service import AIService
from app.models import CodingSession, User

def test_ai_service_generates_activity_summary(db):
    user = User(
        email="ai-service@example.com",
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
        )
    )

    db.commit()

    service = AIService(
        provider=MockAIProvider(),
    )

    result = service.generate_activity_summary(
        db=db,
        current_user=user,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )

    assert result.summary
    assert result.focus_areas