from datetime import date
from sqlalchemy.orm import Session
from app.ai.context import build_activity_context, ActivityContext
from app.ai.provider import AIProvider
from app.ai.schemas import ActivitySummaryResponse
from app.models import User
from app.config import AI_STREAMING_ENABLED

class AIService:
    def __init__(self, provider: AIProvider):
        self.provider = provider

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

        return self.provider.generate_activity_summary(context)

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

        async for chunk in self.provider.generate_activity_summary_stream(context):
            yield chunk