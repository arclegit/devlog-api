from app.rag.mock_provider import MockEmbeddingProvider
from app.rag.openai_provider import OpenAIEmbeddingProvider
from app.rag.provider import EmbeddingProvider
from app.config import EMBEDDING_PROVIDER, AI_API_KEY, EMBEDDING_MODEL, AI_TIMEOUT_SECONDS


def create_embedding_provider() -> EmbeddingProvider:
    if EMBEDDING_PROVIDER == "mock":
        return MockEmbeddingProvider()

    if EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddingProvider(
            api_key=AI_API_KEY,
            model=EMBEDDING_MODEL,
            timeout_seconds=AI_TIMEOUT_SECONDS,
        )

    raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")