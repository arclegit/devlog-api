from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class SessionCreate(BaseModel):
    project_name: str
    language: str
    started_at: datetime
    ended_at: datetime | None = None
    description: str | None = None


class SessionUpdate(BaseModel):
    project_name: str | None = None
    language: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    description: str | None = None


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

    class Config:
        from_attributes = True