from app.ai.context import ActivityContext
from app.ai.mock_provider import MockAIProvider


def test_mock_ai_provider():
    context = ActivityContext(
        total_sessions=5,
        total_coding_seconds=18000,
        average_session_seconds=3600,
        languages=[
            {
                "language": "Python",
                "total_sessions": 4,
                "total_coding_seconds": 14400,
            }
        ],
        projects=[
            {
                "project_name": "DevLog API",
                "total_sessions": 5,
                "total_coding_seconds": 18000,
            }
        ],
        daily_activity=[],
    )

    provider = MockAIProvider()

    result = provider.generate_activity_summary(context)

    assert result.summary
    assert result.focus_areas == ["Python"]
    assert len(result.patterns) == 2