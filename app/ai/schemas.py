from datetime import date

from pydantic import BaseModel, Field, model_validator


class ActivitySummaryRequest(BaseModel):
    start_date: date = Field(
        description="First date included in the activity summary.",
    )
    end_date: date = Field(
        description="Last date included in the activity summary.",
    )

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date > self.end_date:
            raise ValueError(
                "start_date must be earlier than or equal to end_date"
            )
        return self


class ActivitySummaryResponse(BaseModel):
    summary: str = Field(
        description="AI-generated interpretation of the user's development activity.",
    )
    focus_areas: list[str] = Field(
        description="Main development areas identified from the activity data.",
    )
    patterns: list[str] = Field(
        description="Notable patterns identified from the activity data.",
    )