from sqlalchemy import text
from sqlalchemy.orm import Session

from app.rag.chunking import chunk_text
from app.rag.factory import create_embedding_provider
from app.rag.provider import EmbeddingProvider
from app.rag.schemas import SearchRequest


class RAGService:
    def __init__(self, provider: EmbeddingProvider | None = None):
        self.provider = provider or create_embedding_provider()

    # ---------- ingestion ----------

    def ingest_document(self, db: Session, user_id: int, title: str,
                        content: str, source_type: str) -> int:
        """Create a document, chunk it, embed the chunks, insert rows."""
        from app.models import Document, DocumentChunk

        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("document content is empty")

        doc = Document(user_id=user_id, title=title, source_type=source_type)
        db.add(doc)
        db.flush()  # get doc.id

        vectors = self.provider.embed_texts(chunks)

        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    user_id=user_id,
                    chunk_index=index,
                    content=chunk,
                    embedding=vector,
                )
            )
        db.commit()
        return doc.id

    def delete_document(self, db: Session, user_id: int, document_id: int) -> bool:
        from app.models import Document, DocumentChunk

        doc = db.query(Document).filter(
            Document.id == document_id, Document.user_id == user_id
        ).first()
        if doc is None:
            return False
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.delete(doc)
        db.commit()
        return True

    def index_sessions(self, db: Session, user_id: int, start_at, end_at) -> int:
        """Embed session descriptions (project notes) as RAG documents."""
        from app.models import CodingSession, Document

        sessions = (
            db.query(CodingSession)
            .filter(
                CodingSession.user_id == user_id,
                CodingSession.started_at >= start_at,
                CodingSession.started_at <= end_at,
                CodingSession.description.isnot(None),
                CodingSession.description != "",
            )
            .all()
        )

        # Skip sessions that were already indexed (idempotent by title).
        existing = {
            d.title
            for d in db.query(Document).filter(
                Document.user_id == user_id, Document.source_type == "session"
            )
        }

        indexed = 0
        for session in sessions:
            title = f"Session {session.id}: {session.project_name}"
            if title in existing:
                continue
            self.ingest_document(
                db=db,
                user_id=user_id,
                title=title,
                content=(
                    f"Project: {session.project_name}\n"
                    f"Language: {session.language}\n"
                    f"Started: {session.started_at.isoformat()}\n"
                    f"Notes: {session.description}"
                ),
                source_type="session",
            )
            indexed += 1
        return indexed

    # ---------- hybrid retrieval ----------

    def hybrid_search(self, db: Session, user_id: int,
                      query: str, top_k: int = 5) -> list[tuple[int, float]]:
        """
        Returns (chunk_id, fused_score) using Reciprocal Rank Fusion of:
          - pgvector cosine top-50
          - Postgres full-text ts_rank top-50
        """
        query_vector = self.provider.embed_texts([query])[0]

        sql = text(
            """
            WITH vector_results AS (
                SELECT dc.id AS chunk_id,
                       ROW_NUMBER() OVER (
                           ORDER BY dc.embedding <=> CAST(:qv AS vector)
                       ) AS rank
                FROM document_chunks dc
                WHERE dc.user_id = :user_id
                ORDER BY dc.embedding <=> CAST(:qv AS vector)
                LIMIT 50
            ),
            fts_results AS (
                SELECT dc.id AS chunk_id,
                       ROW_NUMBER() OVER (
                           ORDER BY ts_rank(dc.tsv, plainto_tsquery('english', :q)) DESC
                       ) AS rank
                FROM document_chunks dc
                WHERE dc.user_id = :user_id
                  AND dc.tsv @@ plainto_tsquery('english', :q)
                ORDER BY ts_rank(dc.tsv, plainto_tsquery('english', :q)) DESC
                LIMIT 50
            )
            SELECT chunk_id,
                   COALESCE(1.0 / (60 + rank), 0.0) +
                   COALESCE((SELECT 1.0 / (60 + f.rank) FROM fts_results f
                             WHERE f.chunk_id = v.chunk_id), 0.0) AS rrf_score
            FROM vector_results v
            UNION
            SELECT f.chunk_id,
                   COALESCE(1.0 / (60 + f.rank), 0.0) +
                   COALESCE((SELECT 1.0 / (60 + v.rank) FROM vector_results v
                             WHERE v.chunk_id = f.chunk_id), 0.0) AS rrf_score
            FROM fts_results f
            ORDER BY rrf_score DESC
            LIMIT :top_k
            """
        )

        rows = db.execute(
            sql,
            {
                "qv": "[" + ",".join(f"{x:.6f}" for x in query_vector) + "]",
                "q": query,
                "user_id": user_id,
                "top_k": top_k,
            },
        ).fetchall()

        return [(row[0], float(row[1])) for row in rows]

    def retrieve_chunks(self, db: Session, user_id: int,
                         query: str, top_k: int = 5) -> list[dict]:
        """Hybrid search joined back to chunk + document rows."""
        results = self.hybrid_search(db=db, user_id=user_id, query=query, top_k=top_k)
        if not results:
            return []

        chunk_ids = [chunk_id for chunk_id, _ in results]
        scores = dict(results)

        from app.models import Document, DocumentChunk

        rows = (
            db.query(DocumentChunk, Document)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(DocumentChunk.id.in_(chunk_ids))
            .all()
        )

        out = []
        for chunk, doc in rows:
            out.append(
                {
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "title": doc.title,
                    "content": chunk.content,
                    "score": scores.get(chunk.id, 0.0),
                }
            )
        out.sort(key=lambda item: item["score"], reverse=True)
        return out