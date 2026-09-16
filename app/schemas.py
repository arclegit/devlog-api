from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class SessionCreate(BaseModel):
    project_name: str = Field(min_length=1)
    language: str = Field(min_length=1)
    started_at: datetime
    ended_at: datetime | None = None
    description: str | None = None

    @field_validator("project_name", "language")
    @classmethod
    def validate_text_fields(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("field must not be empty")

        return value

    @model_validator(mode="after")
    def validate_timestamps(self):
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError(
                "ended_at must be greater than or equal to started_at"
            )

        return self


class SessionUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1)
    language: str | None = Field(default=None, min_length=1)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    description: str | None = None

    @field_validator("project_name", "language")
    @classmethod
    def validate_text_fields(cls, value: str | None):
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("field must not be empty")

        return value


class SessionResponse(BaseModel):
    id: int
    user_id: int
    project_name: str
    language: str
    started_at: datetime
    ended_at: datetime | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AnalyticsSummaryResponse(BaseModel):
    total_sessions: int
    total_coding_seconds: float
    average_session_seconds: float

class LanguageAnalyticsResponse(BaseModel):
    language: str
    total_sessions: int
    total_coding_seconds: float

class ProjectAnalyticsResponse(BaseModel):
    project_name: str
    total_sessions: int
    total_coding_seconds: float

class DailyAnalyticsResponse(BaseModel):
    date: str
    total_sessions: int
    total_coding_seconds: float

class WeeklyAnalyticsResponse(BaseModel):
    week: str
    total_sessions: int
    total_coding_seconds: float