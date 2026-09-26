from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from app.rag.exceptions import EmbeddingProviderError
from app.rag.provider import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, timeout_seconds: float):
        if not api_key:
            raise EmbeddingProviderError(
                status_code=503,
                message="Embedding service is not configured.",
            )
        self.model = model
        self.client = OpenAI(api_key=api_key, timeout=timeout_seconds)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.EMBEDDING_DIMENSIONS,
            )
        except APITimeoutError as exc:
            raise EmbeddingProviderError(
                status_code=504, message="Embedding service timed out."
            ) from exc
        except RateLimitError as exc:
            raise EmbeddingProviderError(
                status_code=503, message="Embedding service is temporarily unavailable."
            ) from exc
        except APIError as exc:
            raise EmbeddingProviderError(
                status_code=502, message="Embedding service failed."
            ) from exc

        if response.data is None or len(response.data) != len(texts):
            raise EmbeddingProviderError(
                status_code=502, message="Embedding service returned an invalid response."
            )

        # The API may return embeddings out of input order.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]