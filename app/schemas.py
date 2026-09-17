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
    email: EmailStr = Field(
        description="Email address used to create the user account.",
    )
    password: str = Field(
        min_length=8,
        description="Account password. Must contain at least 8 characters.",
    )


class UserResponse(BaseModel):
    id: int = Field(
        description="Unique identifier of the user.",
    )
    email: EmailStr = Field(
        description="Email address associated with the user account.",
    )

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str = Field(
        description="JWT access token used to authenticate protected requests.",
    )
    token_type: str = Field(
        description="Authentication scheme used with the access token.",
    )


class SessionCreate(BaseModel):
    project_name: str = Field(
        min_length=1,
        description="Name of the project worked on during the session.",
    )
    language: str = Field(
        min_length=1,
        description="Programming language used during the session.",
    )
    started_at: datetime = Field(
        description="Time when the coding session started.",
    )
    ended_at: datetime | None = Field(
        default=None,
        description=(
            "Time when the coding session ended. "
            "Null represents an active session."
        ),
    )
    description: str | None = Field(
        default=None,
        description="Optional notes about the coding session.",
    )

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
    project_name: str | None = Field(
        default=None,
        min_length=1,
        description="Updated project name.",
    )
    language: str | None = Field(
        default=None,
        min_length=1,
        description="Updated programming language.",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Updated session start time.",
    )
    ended_at: datetime | None = Field(
        default=None,
        description=(
            "Updated session end time. "
            "Set to null to represent an active session."
        ),
    )
    description: str | None = Field(
        default=None,
        description="Updated optional notes about the coding session.",
    )

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
    id: int = Field(
        description="Unique identifier of the coding session.",
    )
    user_id: int = Field(
        description="Identifier of the user who owns the session.",
    )
    project_name: str = Field(
        description="Name of the project worked on.",
    )
    language: str = Field(
        description="Programming language used during the session.",
    )
    started_at: datetime = Field(
        description="Time when the coding session started.",
    )
    ended_at: datetime | None = Field(
        description="Time when the coding session ended, or null if active.",
    )
    description: str | None = Field(
        description="Optional notes about the coding session.",
    )
    created_at: datetime = Field(
        description="Time when the session record was created.",
    )
    updated_at: datetime = Field(
        description="Time when the session record was last updated.",
    )

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummaryResponse(BaseModel):
    total_sessions: int = Field(
        description="Number of completed coding sessions.",
    )
    total_coding_seconds: float = Field(
        description="Total coding time from completed sessions, in seconds.",
    )
    average_session_seconds: float = Field(
        description="Average completed session duration, in seconds.",
    )


class LanguageAnalyticsResponse(BaseModel):
    language: str = Field(
        description="Programming language used.",
    )
    total_sessions: int = Field(
        description="Number of completed sessions using this language.",
    )
    total_coding_seconds: float = Field(
        description="Total completed coding time for this language, in seconds.",
    )


class ProjectAnalyticsResponse(BaseModel):
    project_name: str = Field(
        description="Name of the project.",
    )
    total_sessions: int = Field(
        description="Number of completed sessions for this project.",
    )
    total_coding_seconds: float = Field(
        description="Total completed coding time for this project, in seconds.",
    )


class DailyAnalyticsResponse(BaseModel):
    date: str = Field(
        description="Calendar date represented as YYYY-MM-DD.",
    )
    total_sessions: int = Field(
        description="Number of completed sessions started on this date.",
    )
    total_coding_seconds: float = Field(
        description="Total completed coding time for this date, in seconds.",
    )


class WeeklyAnalyticsResponse(BaseModel):
    week: str = Field(
        description="Week represented by the API's weekly grouping value.",
    )
    total_sessions: int = Field(
        description="Number of completed sessions in this week.",
    )
    total_coding_seconds: float = Field(
        description="Total completed coding time for this week, in seconds.",
    )