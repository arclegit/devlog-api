from app.ai.context import ActivityContext
from app.ai.provider import AIProvider
from app.ai.schemas import ActivitySummaryResponse


class MockAIProvider(AIProvider):
    def generate_activity_summary(
        self,
        context: ActivityContext,
    ) -> ActivitySummaryResponse:
        focus_areas = [
            item["language"]
            for item in context.languages[:3]
        ]

        patterns = []

        if context.total_sessions > 0:
            patterns.append(
                f"{context.total_sessions} completed coding sessions "
                "were recorded during the selected period."
            )

        if context.projects:
            patterns.append(
                f"Most activity was associated with "
                f"{context.projects[0]['project_name']}."
            )

        return ActivitySummaryResponse(
            summary=(
                "Development activity was recorded across "
                f"{context.total_sessions} completed sessions."
            ),
            focus_areas=focus_areas,
            patterns=patterns,
        )