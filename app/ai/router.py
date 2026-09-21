from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.factory import create_ai_provider
from app.ai.schemas import (
    ActivitySummaryRequest,
    ActivitySummaryResponse,
)
from app.ai.service import AIService
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User


router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


def get_ai_service() -> AIService:
    return AIService(
        provider=create_ai_provider(),
    )


@router.post(
    "/activity-summary",
    response_model=ActivitySummaryResponse,
    summary="Generate an AI activity summary",
    description=(
        "Generate an interpretation of the authenticated user's "
        "development activity for a requested date range."
    ),
)
def generate_activity_summary(
    request: ActivitySummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    return ai_service.generate_activity_summary(
        db=db,
        current_user=current_user,
        start_date=request.start_date,
        end_date=request.end_date,
    )