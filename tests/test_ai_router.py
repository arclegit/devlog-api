from datetime import date

from app.ai.router import get_ai_service
from app.ai.exceptions import AIProviderError
from app.ai.service import AIService
from app.models import CodingSession, User
from app.rate_limit import limiter
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


class FailingAIService:
    def generate_activity_summary(self, **kwargs):
        raise AIProviderError(
            status_code=503,
            message="AI service is temporarily unavailable.",
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


def test_activity_summary_provider_error_uses_standard_envelope(client, db):
    user = User(
        email="ai-provider-error@example.com",
        password_hash="test-hash",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client.app.dependency_overrides[get_ai_service] = lambda: FailingAIService()
    response = client.post(
        "/ai/activity-summary",
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
        json={"start_date": "2026-09-01", "end_date": "2026-09-20"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "503"
    assert response.json()["error"]["message"] == "AI service is temporarily unavailable."
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]

    client.app.dependency_overrides.pop(get_ai_service, None)


def test_activity_summary_is_rate_limited(client, db):
    user = User(
        email="ai-rate-limit@example.com",
        password_hash="test-hash",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client.app.dependency_overrides[get_ai_service] = lambda: TestAIService()
    limiter.enabled = True
    limiter._storage.reset()

    try:
        responses = [
            client.post(
                "/ai/activity-summary",
                headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
                json={"start_date": "2026-09-01", "end_date": "2026-09-20"},
            )
            for _ in range(6)
        ]
    finally:
        limiter._storage.reset()
        limiter.enabled = False
        client.app.dependency_overrides.pop(get_ai_service, None)

    assert [response.status_code for response in responses[:5]] == [200] * 5
    assert responses[5].status_code == 429
    assert responses[5].json()["error"]["code"] == "429"