from datetime import date
from sqlalchemy.orm import Session
from app.ai.context import build_activity_context, ActivityContext
from app.ai.provider import AIProvider
from app.ai.schemas import ActivitySummaryResponse, Citation
from app.models import User
from app.config import AI_STREAMING_ENABLED, RAG_TOP_K
from app.rag.factory import create_embedding_provider
from app.rag.service import RAGService

class AIService:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    def _retrieve_context(self, db: Session, current_user: User,
                          start_date: date, end_date: date) -> list[dict]:
        """Hybrid-retrieve the user's notes relevant to the summary period."""
        try:
            rag = RAGService(provider=create_embedding_provider())
            query = (
                f"development activity notes between {start_date.isoformat()} "
                f"and {end_date.isoformat()}"
            )
            return rag.retrieve_chunks(
                db=db, user_id=current_user.id, query=query, top_k=RAG_TOP_K
            )
        except Exception:
            # RAG is a enhancement: summaries still work without it.
            return []

    def generate_activity_summary(
        self,
        db: Session,
        current_user: User,
        start_date: date,
        end_date: date,
    ) -> ActivitySummaryResponse:
        context = build_activity_context(
            db=db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )
        context.retrieved_chunks = self._retrieve_context(
            db, current_user, start_date, end_date
        )

        response = self.provider.generate_activity_summary(context)

        # Validate citations: drop any citation that was not actually retrieved.
        valid_ids = {c["chunk_id"] for c in context.retrieved_chunks}
        by_id = {c["chunk_id"]: c for c in context.retrieved_chunks}
        response.citations = [
            citation for citation in response.citations
            if citation.chunk_id in valid_ids
        ]
        for citation in response.citations:
            citation.title = by_id[citation.chunk_id]["title"]
            citation.document_id = by_id[citation.chunk_id]["document_id"]

        return response

      

    async def generate_activity_summary_stream(
        self,
        db: Session,
        current_user: User,
        start_date: date,
        end_date: date,
    ):
        context = build_activity_context(
            db=db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
        )

        context.retrieved_chunks = self._retrieve_context(
            db, current_user, start_date, end_date
        )

        async for chunk in self.provider.generate_activity_summary_stream(context):
            yield chunk