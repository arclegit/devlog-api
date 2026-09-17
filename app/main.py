from fastapi import FastAPI

from app.analytics import router as analytics_router
from app.auth import router as auth_router
from app.sessions import router as sessions_router


app = FastAPI(
    title="DevLog API",
    description=(
        "Developer activity logging and analytics REST API. "
        "DevLog allows authenticated developers to record coding "
        "sessions and analyze their development activity."
    ),
    version="0.1.0",
)


app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(analytics_router)


@app.get(
    "/",
    summary="Check API status",
    description="Returns a simple message confirming that the DevLog API is running.",
)
def root():
    return {"message": "DevLog API is running"}