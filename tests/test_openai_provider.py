import json
from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, APITimeoutError, RateLimitError

from app.ai.context import ActivityContext
from app.ai.exceptions import AIProviderError
from app.ai.openai_provider import OpenAIProvider
from app.ai.schemas import ActivitySummaryResponse


VALID_JSON = json.dumps({
    "summary": "You worked on Python.",
    "focus_areas": ["Python"],
    "patterns": ["5 sessions completed."],
})


def _context():
    return ActivityContext(
        total_sessions=5,
        total_coding_seconds=18000,
        average_session_seconds=3600,
        languages=[{"language": "Python", "total_sessions": 5,
                    "total_coding_seconds": 18000}],
        projects=[{"project_name": "DevLog API", "total_sessions": 5,
                    "total_coding_seconds": 18000}],
        daily_activity=[],
    )


def _mock_response(content=VALID_JSON):
    """Build a fake chat.completions response object."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


def _provider():
    with patch("app.ai.openai_provider.AI_API_KEY", "test-api-key"), \
         patch("app.ai.openai_provider.OpenAI"), \
         patch("app.ai.openai_provider.AsyncOpenAI"):
        provider = OpenAIProvider()
    provider.client = MagicMock()
    provider.async_client = MagicMock()
    return provider



class TestOpenAIProvider:
    def test_returns_structured_summary(self):
        provider = _provider()
        provider.client.chat.completions.create.return_value = _mock_response()

        result = provider.generate_activity_summary(_context())

        assert result.summary == "You worked on Python."
        assert result.focus_areas == ["Python"]

    def test_rejects_missing_structured_output(self):
        provider = _provider()
        provider.client.chat.completions.create.return_value = _mock_response(content=None)

        with pytest.raises(AIProviderError) as exc_info:
            provider.generate_activity_summary(_context())
        assert exc_info.value.status_code == 502

    def test_rejects_invalid_json(self):
        provider = _provider()
        provider.client.chat.completions.create.return_value = _mock_response(content="not json")

        with pytest.raises(AIProviderError) as exc_info:
            provider.generate_activity_summary(_context())
        assert exc_info.value.status_code == 502

    def test_maps_timeout_to_safe_error(self):
        provider = _provider()
        provider.client.chat.completions.create.side_effect = APITimeoutError(
            request=MagicMock()
        )

        with pytest.raises(AIProviderError) as exc_info:
            provider.generate_activity_summary(_context())
        assert exc_info.value.status_code == 504

    def test_maps_rate_limit_to_safe_error(self):
        provider = _provider()
        provider.client.chat.completions.create.side_effect = RateLimitError(
            message="rate limited", response=MagicMock(), body=None
        )

        with pytest.raises(AIProviderError) as exc_info:
            provider.generate_activity_summary(_context())
        assert exc_info.value.status_code == 503

    def test_maps_api_error_to_safe_error(self):
        provider = _provider()
        provider.client.chat.completions.create.side_effect = APIError(
            message="boom", request=MagicMock(), body=None
        )

        with pytest.raises(AIProviderError) as exc_info:
            provider.generate_activity_summary(_context())
        assert exc_info.value.status_code == 502