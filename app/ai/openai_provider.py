import json

from openai import (
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    OpenAI,
    RateLimitError,
)

from pydantic import ValidationError as PydanticValidationError
from app.ai.context import ActivityContext
from app.ai.exceptions import AIProviderError
from app.ai.provider import AIProvider
from app.ai.schemas import ActivitySummaryResponse
from app.config import AI_API_KEY, AI_BASE_URL, AI_MODEL, AI_TIMEOUT_SECONDS

class OpenAIProvider(AIProvider):
    def __init__(self):
        if not AI_API_KEY:
            raise AIProviderError(
                status_code=503,
                message="AI service is not configured.",
            )

        self.client = OpenAI(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL,
            timeout=AI_TIMEOUT_SECONDS,
        )

        self.async_client = AsyncOpenAI(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL,
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
            response = self.client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "activity_summary",
                        "schema": ActivitySummaryResponse.model_json_schema(),
                    },
                },
            )

            # === FIX FOR YOUR REQUIREMENT ===
            try:
                return ActivitySummaryResponse.model_validate_json(
                    response.choices[0].message.content
                )
            except (PydanticValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise AIProviderError(
                    status_code=502,
                    message="AI service returned an invalid response.",
                ) from None
            # === END FIX ===

        except AIProviderError:
            raise

        except APITimeoutError as exc:
            raise AIProviderError(
                status_code=504,
                message="AI service timed out.",
            ) from exc

        except RateLimitError as exc:
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

        user_notes = [
            {"chunk_id": c["chunk_id"], "title": c["title"], "content": c["content"]}
            for c in context.retrieved_chunks
        ]

        system_prompt = """
        You are an assistant that analyzes software development activity data.
        Use only the activity data provided by the application and, when
        grounding the interpretation, the user's own notes/documents.
        Rules:
        1. Do not invent statistics.
        2. Do not invent programming languages or projects.
        3. When you rely on a note, cite it by chunk_id in the citations field.
        4. Never cite a chunk_id that was not supplied.
        5. If no notes are supplied, return an empty citations list.
        6. Keep the summary concise and factual.
        7. Return the requested structured response.
        """

        user_prompt = (
            "Analyze the following development activity data and produce "
            "an activity summary.\n\n"
            f"ACTIVITY DATA:\n{json.dumps(activity_data, default=str)}\n\n"
        )
        if user_notes:
            user_prompt += (
                f"USER NOTES (cite chunk_id when used):\n"
                f"{json.dumps(user_notes, default=str)}\n\n"
            )
        user_prompt += "Produce the structured summary now."

        try:
            stream = await self.async_client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except APITimeoutError as exc:
            raise AIProviderError(status_code=504, message="AI service timed out.") from exc
        except RateLimitError as exc:
            print("OPENAI STREAM RATE LIMIT ERROR:", f"status={getattr(exc, 'status_code', None)}")
            raise AIProviderError(status_code=503, message="AI service is temporarily unavailable.") from exc
        except APIError as exc:
            print("OPENAI STREAM API ERROR:", f"status={getattr(exc, 'status_code', None)}")
            raise AIProviderError(status_code=502, message="AI service failed to generate a summary.") from exc