from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, description="Title of the document.")
    content: str = Field(min_length=1, description="Full text content of the document.")
    source_type: str = Field(
        default="note",
        description="Origin of the document, for example note, doc, session.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "API auth design",
                "content": "We chose JWT bearer auth with 30-minute expiry...",
                "source_type": "note",
            }
        }
    )


class Citation(BaseModel):
    chunk_id: int = Field(description="Identifier of the cited document chunk.")
    document_id: int = Field(description="Identifier of the cited document.")
    title: str = Field(description="Title of the cited document.")
    snippet: str = Field(description="Short excerpt of the cited chunk.")


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    score: float = Field(description="Fused relevance score; higher is better.")

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: int
    title: str
    source_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Natural-language search query.")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return.")


class SearchResponse(BaseModel):
    results: list[DocumentChunkResponse] = Field(
        description="Hybrid (vector + full-text) ranked results."
    )


class IndexSessionsRequest(BaseModel):
    """Embed session descriptions as documents for RAG."""

    start_date: datetime = Field(description="Index sessions started at/after this time.")
    end_date: datetime = Field(description="Index sessions started before/at this time.")