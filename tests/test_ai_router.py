from datetime import date

from app.ai.router import get_ai_service
from app.ai.service import AIService
from app.models import CodingSession, User
from app.security import create_access_token


class TestAIService:
    def generate_activity_summary(
        self,
        db,
        current_user,
        start_date,
        end_date,
    ):
        from app.ai.schemas import ActivitySummaryResponse

        return ActivitySummaryResponse(
            summary="Test summary",
            focus_areas=["Python"],
            patterns=["Backend activity increased."],
        )


def test_activity_summary_endpoint(client, db):
    user = User(
        email="ai-route@example.com",
        password_hash="test-hash",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    app = client.app

    app.dependency_overrides[get_ai_service] = (
        lambda: TestAIService()
    )

    response = client.post(
        "/ai/activity-summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "start_date": "2026-09-01",
            "end_date": "2026-09-20",
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "Test summary"

    app.dependency_overrides.pop(
        get_ai_service,
        None,
    )