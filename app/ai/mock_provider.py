from app.ai.context import ActivityContext
from app.ai.provider import AIProvider
from app.ai.schemas import ActivitySummaryResponse, TokenUsage, CostLog, Citation 

class MockAIProvider(AIProvider):
    def generate_activity_summary(
        self,
        context: ActivityContext,
    ) -> ActivitySummaryResponse:
        focus_areas = [item["language"] for item in context.languages[:3]]
        patterns = []

        if context.total_sessions > 0:
            patterns.append(
                f"{context.total_sessions} completed coding sessions were recorded during the selected period."
            )

        if context.projects:
            patterns.append(
                f"Most activity was associated with {context.projects[0]['project_name']}."
            )

        if context.retrieved_chunks:
            patterns.append(
                "The summary was grounded in the user's own notes."
            )

        citations = [
            Citation(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                title=chunk["title"],
                snippet=chunk["content"][:160],
            )
            for chunk in context.retrieved_chunks[:2]
        ]

        return ActivitySummaryResponse(
            summary=f"Development activity was recorded across {context.total_sessions} completed sessions.",
            focus_areas=focus_areas,
            patterns=patterns,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
            cost=CostLog(model="mock", cost=0.0),
            citations=citations,
        )

       

    async def generate_activity_summary_stream(
        self,
        context: ActivityContext,
    ):
        yield "Development activity was recorded across "
        yield f"{context.total_sessions} completed sessions."