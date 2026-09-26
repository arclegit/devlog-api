from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Document, User
from app.rag.exceptions import EmbeddingProviderError
from app.rag.schemas import (
    DocumentCreate,
    DocumentResponse,
    IndexSessionsRequest,
    SearchRequest,
    SearchResponse,
)
from app.rag.service import RAGService
from app.rate_limit import limiter

router = APIRouter(prefix="/rag", tags=["RAG"])


def get_rag_service() -> RAGService:
    return RAGService()


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload a document for RAG",
    description="Create a document, chunk and embed its content, and store it for hybrid retrieval.",
)
@limiter.limit("10/minute")
def create_document(
    request: Request,
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    try:
        document_id = rag_service.ingest_document(
            db=db,
            user_id=current_user.id,
            title=document.title,
            content=document.content,
            source_type=document.source_type,
        )
    except EmbeddingProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    doc = db.query(Document).filter(
        Document.id == document_id, Document.user_id == current_user.id
    ).first()
    return _document_response(db, doc)


@router.get(
    "/documents",
    response_model=list[DocumentResponse],
    summary="List RAG documents",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [_document_response(db, doc) for doc in docs]


@router.delete(
    "/documents/{document_id}",
    status_code=204,
    summary="Delete a RAG document",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    if not rag_service.delete_document(db=db, user_id=current_user.id,
                                       document_id=document_id):
        raise HTTPException(status_code=404, detail="Document not found.")


@router.post(
    "/index/sessions",
    summary="Index session notes as RAG documents",
    description="Embed the authenticated user's session descriptions in a date range so AI summaries can cite them.",
)
@limiter.limit("3/minute")
def index_sessions(
    request: Request,
    payload: IndexSessionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    try:
        indexed = rag_service.index_sessions(
            db=db,
            user_id=current_user.id,
            start_at=payload.start_date,
            end_at=payload.end_date,
        )
    except EmbeddingProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return {"indexed_sessions": indexed}


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Hybrid semantic + keyword search",
)
@limiter.limit("20/minute")
def search(
    request: Request,
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    try:
        results = rag_service.retrieve_chunks(
            db=db, user_id=current_user.id,
            query=payload.query, top_k=payload.top_k,
        )
    except EmbeddingProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    from app.rag.schemas import DocumentChunkResponse

    return SearchResponse(
        results=[
            DocumentChunkResponse(
                id=r["chunk_id"],
                document_id=r["document_id"],
                chunk_index=0,
                content=r["content"][:500],
                score=round(r["score"], 6),
            )
            for r in results
        ]
    )


def _document_response(db: Session, doc: Document) -> DocumentResponse:
    from app.models import DocumentChunk

    chunk_count = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc.id)
        .count()
    )
    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        chunk_count=chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )