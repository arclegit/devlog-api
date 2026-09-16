from app.analytics import router as analytics_router
from app.auth import router as auth_router
from app.sessions import router as sessions_router

from fastapi import FastAPI

app = FastAPI(title="DevLog API")

app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {"message": "DevLog API is running"}