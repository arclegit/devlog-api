from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Boundary for embedding generation, mirroring app/ai/provider.py."""

    EMBEDDING_DIMENSIONS = 1536

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError