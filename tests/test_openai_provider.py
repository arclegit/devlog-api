from unittest.mock import Mock, patch

import pytest
from openai import APIError, APITimeoutError, RateLimitError

from app.ai.context import ActivityContext
from app.ai.exceptions import AIProviderError
from app.ai.openai_provider import OpenAIProvider
from app.ai.schemas import ActivitySummaryResponse


@pytest.fixture
def activity_context():
    return ActivityContext(
        total_sessions=2,
        total_coding_seconds=7200,
        average_session_seconds=3600,
        languages=[{"language": "Python"}],
        projects=[{"project_name": "DevLog API"}],
        daily_activity=[],
    )


def test_openai_provider_returns_structured_summary(activity_context):
    parsed_summary = ActivitySummaryResponse(
        summary="Python work focused on DevLog API.",
        focus_areas=["Python"],
        patterns=["Two completed sessions were recorded."],
    )
    client = Mock()
    client.responses.parse.return_value = Mock(output_parsed=parsed_summary)

    with patch("app.ai.openai_provider.AI_API_KEY", "test-key"), patch(
        "app.ai.openai_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIProvider()
        result = provider.generate_activity_summary(activity_context)

    assert result == parsed_summary
    client.responses.parse.assert_called_once()
    assert client.responses.parse.call_args.kwargs["text_format"] is ActivitySummaryResponse


def test_openai_provider_maps_timeout_to_safe_error(activity_context):
    client = Mock()
    client.responses.parse.side_effect = APITimeoutError(request=Mock())

    with patch("app.ai.openai_provider.AI_API_KEY", "test-key"), patch(
        "app.ai.openai_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIProvider()
        with pytest.raises(AIProviderError, match="AI service timed out") as exc_info:
            provider.generate_activity_summary(activity_context)

    assert exc_info.value.status_code == 504


def test_openai_provider_maps_rate_limit_to_safe_error(activity_context):
    client = Mock()
    client.responses.parse.side_effect = RateLimitError(
        "provider limit",
        response=Mock(),
        body=None,
    )

    with patch("app.ai.openai_provider.AI_API_KEY", "test-key"), patch(
        "app.ai.openai_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIProvider()
        with pytest.raises(AIProviderError, match="temporarily unavailable") as exc_info:
            provider.generate_activity_summary(activity_context)

    assert exc_info.value.status_code == 503


def test_openai_provider_maps_api_error_to_safe_error(activity_context):
    client = Mock()
    client.responses.parse.side_effect = APIError(
        "provider error",
        request=Mock(),
        body=None,
    )

    with patch("app.ai.openai_provider.AI_API_KEY", "test-key"), patch(
        "app.ai.openai_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIProvider()
        with pytest.raises(AIProviderError, match="failed to generate") as exc_info:
            provider.generate_activity_summary(activity_context)

    assert exc_info.value.status_code == 502


def test_openai_provider_rejects_missing_structured_output(activity_context):
    client = Mock()
    client.responses.parse.return_value = Mock(output_parsed=None)

    with patch("app.ai.openai_provider.AI_API_KEY", "test-key"), patch(
        "app.ai.openai_provider.OpenAI",
        return_value=client,
    ):
        provider = OpenAIProvider()
        with pytest.raises(AIProviderError, match="invalid response") as exc_info:
            provider.generate_activity_summary(activity_context)

    assert exc_info.value.status_code == 502


def test_openai_provider_rejects_missing_api_key():
    with patch("app.ai.openai_provider.AI_API_KEY", None):
        with pytest.raises(AIProviderError, match="not configured") as exc_info:
            OpenAIProvider()

    assert exc_info.value.status_code == 503
