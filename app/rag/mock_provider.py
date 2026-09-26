import hashlib
import math

from app.rag.provider import EmbeddingProvider


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic pseudo-embeddings so tests run without an API key."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        dimensions = self.EMBEDDING_DIMENSIONS
        vector = []
        for i in range(dimensions):
            digest = hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest()
            value = int.from_bytes(digest[:8], "big") / 2**64 - 0.5
            vector.append(value)
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]