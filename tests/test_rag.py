from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from openai import APIError, APITimeoutError, RateLimitError

from app.models import CodingSession, Document, DocumentChunk, User
from app.rag.chunking import chunk_text
from app.rag.exceptions import EmbeddingProviderError
from app.rag.factory import create_embedding_provider
from app.rag.mock_provider import MockEmbeddingProvider
from app.rag.openai_provider import OpenAIEmbeddingProvider
from app.rag.router import get_rag_service
from app.rag.service import RAGService
from app.security import create_access_token


# =====================================================================
# 1. Chunking Tests
# =====================================================================


def test_chunk_text_empty_and_whitespace():
    assert chunk_text("") == []
    assert chunk_text("   \n\t  ") == []


def test_chunk_text_short_text():
    text = "Short text under limit."
    chunks = chunk_text(text, chunk_size=100)
    assert chunks == [text]


def test_chunk_text_splits_on_boundaries():
    sentence1 = "Sentence one is about coding."
    sentence2 = "Sentence two discusses software testing."
    sentence3 = "Sentence three covers continuous integration."
    full_text = f"{sentence1} {sentence2} {sentence3}"

    chunks = chunk_text(full_text, chunk_size=40, overlap=10)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) > 0


# =====================================================================
# 2. Embedding Provider Tests
# =====================================================================


def test_mock_embedding_provider():
    provider = MockEmbeddingProvider()
    texts = ["hello", "world"]
    vectors = provider.embed_texts(texts)

    assert len(vectors) == 2
    assert len(vectors[0]) == 1536
    assert len(vectors[1]) == 1536
    # Deterministic output
    assert vectors[0] == provider.embed_texts(["hello"])[0]


def test_openai_embedding_provider_requires_api_key():
    with pytest.raises(EmbeddingProviderError) as exc_info:
        OpenAIEmbeddingProvider(api_key="", model="text-embedding-3-small", timeout_seconds=10.0)
    assert exc_info.value.status_code == 503


def test_openai_embedding_provider_success():
    with patch("app.rag.openai_provider.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_item = MagicMock()
        mock_item.embedding = [0.05] * 1536
        mock_client.embeddings.create.return_value = MagicMock(data=[mock_item])

        provider = OpenAIEmbeddingProvider(
            api_key="test-key", model="text-embedding-3-small", timeout_seconds=10.0
        )
        res = provider.embed_texts(["sample text"])
        assert len(res) == 1
        assert len(res[0]) == 1536


def test_openai_embedding_provider_maps_timeout_error():
    with patch("app.rag.openai_provider.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.side_effect = APITimeoutError(request=MagicMock())

        provider = OpenAIEmbeddingProvider(
            api_key="test-key", model="text-embedding-3-small", timeout_seconds=10.0
        )
        with pytest.raises(EmbeddingProviderError) as exc_info:
            provider.embed_texts(["sample"])
        assert exc_info.value.status_code == 504


def test_openai_embedding_provider_maps_rate_limit_error():
    with patch("app.rag.openai_provider.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.side_effect = RateLimitError(
            message="Rate limit exceeded", response=MagicMock(), body=None
        )

        provider = OpenAIEmbeddingProvider(
            api_key="test-key", model="text-embedding-3-small", timeout_seconds=10.0
        )
        with pytest.raises(EmbeddingProviderError) as exc_info:
            provider.embed_texts(["sample"])
        assert exc_info.value.status_code == 503


def test_openai_embedding_provider_maps_api_error():
    with patch("app.rag.openai_provider.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.side_effect = APIError(
            message="Server error", request=MagicMock(), body=None
        )

        provider = OpenAIEmbeddingProvider(
            api_key="test-key", model="text-embedding-3-small", timeout_seconds=10.0
        )
        with pytest.raises(EmbeddingProviderError) as exc_info:
            provider.embed_texts(["sample"])
        assert exc_info.value.status_code == 502


def test_create_embedding_provider_factory():
    with patch("app.rag.factory.EMBEDDING_PROVIDER", "mock"):
        prov = create_embedding_provider()
        assert isinstance(prov, MockEmbeddingProvider)

    with patch("app.rag.factory.EMBEDDING_PROVIDER", "openai"), \
         patch("app.rag.factory.AI_API_KEY", "test-key"), \
         patch("app.rag.openai_provider.OpenAI"):
        prov = create_embedding_provider()
        assert isinstance(prov, OpenAIEmbeddingProvider)

    with patch("app.rag.factory.EMBEDDING_PROVIDER", "unsupported"):
        with pytest.raises(RuntimeError, match="Unsupported EMBEDDING_PROVIDER"):
            create_embedding_provider()


# =====================================================================
# 3. RAG Service Database Ingestion & Sessions Tests (SQLite)
# =====================================================================


def test_rag_service_ingest_and_delete_document(db):
    user = User(email="rag-service@example.com", password_hash="test-hash", timezone="UTC")
    db.add(user)
    db.commit()

    service = RAGService(provider=MockEmbeddingProvider())

    # Ingest document
    doc_id = service.ingest_document(
        db=db,
        user_id=user.id,
        title="Architecture Guide",
        content="This document covers high-level architectural patterns for Python microservices.",
        source_type="note",
    )
    assert doc_id is not None

    doc = db.query(Document).filter(Document.id == doc_id).first()
    assert doc is not None
    assert doc.title == "Architecture Guide"

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
    assert len(chunks) >= 1
    assert chunks[0].user_id == user.id

    # Test delete
    assert service.delete_document(db=db, user_id=user.id, document_id=doc_id) is True
    assert db.query(Document).filter(Document.id == doc_id).first() is None
    assert db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).first() is None

    # Delete non-existent
    assert service.delete_document(db=db, user_id=user.id, document_id=99999) is False


def test_rag_service_ingest_empty_raises_error(db):
    user = User(email="rag-empty@example.com", password_hash="test-hash", timezone="UTC")
    db.add(user)
    db.commit()

    service = RAGService(provider=MockEmbeddingProvider())
    with pytest.raises(ValueError, match="document content is empty"):
        service.ingest_document(
            db=db,
            user_id=user.id,
            title="Empty",
            content="   ",
            source_type="note",
        )


def test_rag_service_index_sessions(db):
    user = User(email="rag-sessions@example.com", password_hash="test-hash", timezone="UTC")
    db.add(user)
    db.commit()

    start_time1 = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    end_time1 = datetime(2026, 9, 20, 11, 0, tzinfo=timezone.utc)
    session1 = CodingSession(
        user_id=user.id,
        project_name="devlog-api",
        language="Python",
        started_at=start_time1,
        ended_at=end_time1,
        description="Added RAG hybrid search module.",
    )

    start_time2 = datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc)
    end_time2 = datetime(2026, 9, 21, 11, 0, tzinfo=timezone.utc)
    session2 = CodingSession(
        user_id=user.id,
        project_name="devlog-api",
        language="Python",
        started_at=start_time2,
        ended_at=end_time2,
        description="",  # empty description should be ignored
    )
    db.add_all([session1, session2])
    db.commit()

    service = RAGService(provider=MockEmbeddingProvider())
    indexed_count = service.index_sessions(
        db=db,
        user_id=user.id,
        start_at=datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
    )
    assert indexed_count == 1

    # Idempotent re-run
    indexed_again = service.index_sessions(
        db=db,
        user_id=user.id,
        start_at=datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc),
    )
    assert indexed_again == 0


# =====================================================================
# 4. RAG API Router Tests
# =====================================================================


def _create_authenticated_user(db, client):
    user = User(
        email="rag-router@example.com",
        password_hash="test-password",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def test_rag_document_crud_endpoints(client, db):
    user, headers = _create_authenticated_user(db, client)

    # Use mock service provider so no external LLM/OpenAI network call is triggered
    service = RAGService(provider=MockEmbeddingProvider())
    client.app.dependency_overrides[get_rag_service] = lambda: service

    try:
        # 1. Ingest document via POST
        response = client.post(
            "/rag/documents",
            headers=headers,
            json={
                "title": "API Documentation",
                "content": "This document outlines all public endpoints and their authentication scopes.",
                "source_type": "note",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "API Documentation"
        assert data["chunk_count"] >= 1
        doc_id = data["id"]

        # 2. List documents via GET
        list_resp = client.get("/rag/documents", headers=headers)
        assert list_resp.status_code == 200
        docs = list_resp.json()
        assert len(docs) >= 1
        assert any(d["id"] == doc_id for d in docs)

        # 3. Delete document via DELETE
        del_resp = client.delete(f"/rag/documents/{doc_id}", headers=headers)
        assert del_resp.status_code == 204

        # 4. Delete 404
        del_404 = client.delete(f"/rag/documents/{doc_id}", headers=headers)
        assert del_404.status_code == 404
    finally:
        client.app.dependency_overrides.pop(get_rag_service, None)


def test_rag_create_document_empty_content_422(client, db):
    _, headers = _create_authenticated_user(db, client)
    response = client.post(
        "/rag/documents",
        headers=headers,
        json={"title": "Empty Doc", "content": "   ", "source_type": "note"},
    )
    assert response.status_code == 422


def test_rag_create_document_embedding_error_handling(client, db):
    _, headers = _create_authenticated_user(db, client)

    mock_service = MagicMock()
    mock_service.ingest_document.side_effect = EmbeddingProviderError(
        status_code=503, message="Embedding provider offline."
    )

    client.app.dependency_overrides[get_rag_service] = lambda: mock_service
    try:
        response = client.post(
            "/rag/documents",
            headers=headers,
            json={"title": "Doc", "content": "Valid content.", "source_type": "note"},
        )
        assert response.status_code == 503
        assert response.json()["error"]["message"] == "Embedding provider offline."
    finally:
        client.app.dependency_overrides.pop(get_rag_service, None)


def test_rag_index_sessions_endpoint(client, db):
    user, headers = _create_authenticated_user(db, client)

    mock_service = MagicMock()
    mock_service.index_sessions.return_value = 3
    client.app.dependency_overrides[get_rag_service] = lambda: mock_service
    try:
        response = client.post(
            "/rag/index/sessions",
            headers=headers,
            json={
                "start_date": "2026-09-01T00:00:00Z",
                "end_date": "2026-09-26T00:00:00Z",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"indexed_sessions": 3}
    finally:
        client.app.dependency_overrides.pop(get_rag_service, None)


def test_rag_search_endpoint(client, db):
    user, headers = _create_authenticated_user(db, client)

    mock_service = MagicMock()
    mock_service.retrieve_chunks.return_value = [
        {
            "chunk_id": 1,
            "document_id": 10,
            "title": "Search Guide",
            "content": "Full text and vector retrieval combined.",
            "score": 0.0325,
        }
    ]

    client.app.dependency_overrides[get_rag_service] = lambda: mock_service
    try:
        response = client.post(
            "/rag/search",
            headers=headers,
            json={"query": "hybrid retrieval", "top_k": 3},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["document_id"] == 10
        assert results[0]["score"] == 0.0325
    finally:
        client.app.dependency_overrides.pop(get_rag_service, None)
