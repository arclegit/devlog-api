from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import AccountDelete, PasswordChange, Token, UserRegister, UserResponse
from app.security import create_access_token, hash_password, verify_password
from app.rate_limit import limiter


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new DevLog user account using an email address and password. "
        "The password is securely hashed before it is stored."
    ),
    responses={
        409: {
            "description": "The email address is already registered."
        },
    },
)
@limiter.limit("5/minute")
def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        timezone=user_data.timezone,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Log in",
    description=(
        "Authenticate a user with their email address and password "
        "and return a JWT access token. "
        "The OAuth2 form field named 'username' represents the user's email address."
    ),
    responses={
        401: {
            "description": "Invalid email or password."
        },
    },
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == form_data.username, User.deleted_at.is_(None))
    )

    if not user or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description=(
        "Return the account information of the currently authenticated user."
    ),
    responses={
        401: {
            "description": "Authentication credentials are missing or invalid."
        },
    },
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT, summary="Change account password")
def change_password(password_data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, summary="Soft-delete the current account")
def delete_account(delete_data: AccountDelete, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(delete_data.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect")
    current_user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
