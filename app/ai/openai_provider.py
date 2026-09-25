import json

from openai import (
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    OpenAI,
    RateLimitError,
)

from app.ai.context import ActivityContext
from app.ai.exceptions import AIProviderError
from app.ai.provider import AIProvider
from app.ai.schemas import ActivitySummaryResponse
from app.config import AI_API_KEY, AI_MODEL, AI_TIMEOUT_SECONDS


class OpenAIProvider(AIProvider):
    def __init__(self):
        if not AI_API_KEY:
            raise AIProviderError(
                status_code=503,
                message="AI service is not configured.",
            )

        # Sync client for the normal structured summary
        self.client = OpenAI(
            api_key=AI_API_KEY,
            timeout=AI_TIMEOUT_SECONDS,
        )

        # Async client for streaming
        self.async_client = AsyncOpenAI(
            api_key=AI_API_KEY,
            timeout=AI_TIMEOUT_SECONDS,
        )

    def generate_activity_summary(
        self,
        context: ActivityContext,
    ) -> ActivitySummaryResponse:
        activity_data = {
            "total_sessions": context.total_sessions,
            "total_coding_seconds": context.total_coding_seconds,
            "average_session_seconds": context.average_session_seconds,
            "languages": context.languages,
            "projects": context.projects,
            "daily_activity": context.daily_activity,
        }

        system_prompt = """
        You are an assistant that analyzes software development activity data.
        Use only the activity data provided by the application.

        Rules:
        1. Do not invent statistics.
        2. Do not invent programming languages.
        3. Do not invent projects.
        4. Do not claim activity that is not present in the data.
        5. Keep the summary concise and factual.
        6. Identify focus areas only from the supplied language data.
        7. Identify patterns only from the supplied activity data.
        8. Return the requested structured response.
        """

        user_prompt = (
            "Analyze the following development activity data and produce "
            "an activity summary.\n\n"
            f"{json.dumps(activity_data, default=str)}"
        )

        try:
            response = self.client.responses.parse(
                model=AI_MODEL,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                text_format=ActivitySummaryResponse,
            )

            if response.output_parsed is None:
                raise AIProviderError(
                    status_code=502,
                    message="AI service returned an invalid response.",
                )

            return response.output_parsed

        except APITimeoutError as exc:
            raise AIProviderError(
                status_code=504,
                message="AI service timed out.",
            ) from exc

        except RateLimitError as exc:
            # Temporary diagnostic logging.
            # This helps identify exactly why OpenAI returned HTTP 429.
            # Never log the API key.
            print(
                "OPENAI RATE LIMIT ERROR:",
                f"status={getattr(exc, 'status_code', None)}",
                f"response={getattr(exc, 'response', None)}",
                f"body={getattr(exc, 'body', None)}",
                f"code={getattr(exc, 'code', None)}",
            )

            raise AIProviderError(
                status_code=503,
                message="AI service is temporarily unavailable.",
            ) from exc

        except APIError as exc:
            print(
                "OPENAI API ERROR:",
                f"status={getattr(exc, 'status_code', None)}",
                f"response={getattr(exc, 'response', None)}",
                f"body={getattr(exc, 'body', None)}",
            )

            raise AIProviderError(
                status_code=502,
                message="AI service failed to generate a summary.",
            ) from exc

    async def generate_activity_summary_stream(
        self,
        context: ActivityContext,
    ):
        activity_data = {
            "total_sessions": context.total_sessions,
            "total_coding_seconds": context.total_coding_seconds,
            "average_session_seconds": context.average_session_seconds,
            "languages": context.languages,
            "projects": context.projects,
            "daily_activity": context.daily_activity,
        }

        system_prompt = """
        You are an assistant that analyzes software development activity data.
        Use only the activity data provided by the application.

        Rules:
        1. Do not invent statistics.
        2. Do not invent programming languages.
        3. Do not invent projects.
        4. Do not claim activity that is not present in the data.
        5. Keep the summary concise and factual.
        6. Identify focus areas only from the supplied language data.
        7. Identify patterns only from the supplied activity data.
        8. Return the requested structured response.
        """

        user_prompt = (
            "Analyze the following development activity data and produce "
            "an activity summary.\n\n"
            f"{json.dumps(activity_data, default=str)}"
        )

        try:
            stream = await self.async_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except APITimeoutError as exc:
            raise AIProviderError(
                status_code=504,
                message="AI service timed out.",
            ) from exc

        except RateLimitError as exc:
            # Keep streaming behavior unchanged.
            # Diagnostic details are logged if streaming ever hits 429.
            print(
                "OPENAI STREAM RATE LIMIT ERROR:",
                f"status={getattr(exc, 'status_code', None)}",
                f"response={getattr(exc, 'response', None)}",
                f"body={getattr(exc, 'body', None)}",
                f"code={getattr(exc, 'code', None)}",
            )

            raise AIProviderError(
                status_code=503,
                message="AI service is temporarily unavailable.",
            ) from exc

        except APIError as exc:
            print(
                "OPENAI STREAM API ERROR:",
                f"status={getattr(exc, 'status_code', None)}",
                f"response={getattr(exc, 'response', None)}",
                f"body={getattr(exc, 'body', None)}",
            )

            raise AIProviderError(
                status_code=502,
                message="AI service failed to generate a summary.",
            ) from exc
        