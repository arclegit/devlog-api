from app.ai.mock_provider import MockAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.provider import AIProvider
from app.config import AI_PROVIDER


def create_ai_provider() -> AIProvider:
    if AI_PROVIDER == "mock":
        return MockAIProvider()

    if AI_PROVIDER in ("openai", "gemini"):
        return OpenAIProvider()

    raise RuntimeError(
        f"Unsupported AI_PROVIDER: {AI_PROVIDER}"
    )
   
