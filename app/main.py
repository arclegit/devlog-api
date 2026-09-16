from app.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI(title="DevLog API")
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "DevLog API is running"}