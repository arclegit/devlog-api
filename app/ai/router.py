from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.ai.exceptions import AIProviderError
from app.ai.factory import create_ai_provider
from app.ai.schemas import ActivitySummaryRequest, ActivitySummaryResponse
from app.ai.service import AIService
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.rate_limit import limiter
from app.config import AI_STREAMING_ENABLED

router = APIRouter(prefix="/ai", tags=["AI"])

def get_ai_service() -> AIService:
    return AIService(provider=create_ai_provider())

@router.post(
    "/activity-summary",
    response_model=ActivitySummaryResponse,
    summary="Generate an AI activity summary",
    description="Generate an interpretation of the authenticated user's development activity for a requested date range.",
)
@limiter.limit("5/minute")
def generate_activity_summary(
    request: Request,
    summary_request: ActivitySummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    try:
        return ai_service.generate_activity_summary(
            db=db,
            current_user=current_user,
            start_date=summary_request.start_date,
            end_date=summary_request.end_date,
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc

@router.post(
    "/activity-summary-stream",
    summary="Generate a streaming AI activity summary",
    description="Generate a streaming interpretation of the authenticated user's development activity for a requested date range.",
)
@limiter.limit("5/minute")
async def generate_activity_summary_stream(
    request: Request,
    summary_request: ActivitySummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    if not AI_STREAMING_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not enabled.",
        )

    try:
        return StreamingResponse(
            ai_service.generate_activity_summary_stream(
                db=db,
                current_user=current_user,
                start_date=summary_request.start_date,
                end_date=summary_request.end_date,
            ),
            media_type="text/plain",
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        ) from exc