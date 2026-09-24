import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.errors import http_exception_handler, rate_limit_exception_handler, validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.logging import configure_logging
from app.rate_limit import limiter

from app.ai.router import router as ai_router
from app.analytics import router as analytics_router
from app.auth import router as auth_router
from app.sessions import router as sessions_router


app = FastAPI(
    title="DevLog API",
    description=(
        "Developer activity logging and analytics REST API. "
        "DevLog allows authenticated developers to record coding "
        "sessions, analyze their development activity, and generate "
        "AI-powered activity summaries."
    ),
    version="3.0.0",
)
configure_logging()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_middleware(SlowAPIMiddleware)
logger = structlog.get_logger()


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info("request_completed", request_id=request_id, method=request.method, path=request.url.path, status_code=response.status_code, duration_ms=round((time.perf_counter() - started) * 1000, 2))
    return response


app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(analytics_router)
app.include_router(ai_router)


@app.get(
    "/",
    summary="Check API status",
    description="Returns a simple message confirming that the DevLog API is running.",
)
def root():
    return {"message": "DevLog API is running"}


@app.get("/health", tags=["Operations"], summary="Liveness check")
def health():
    return {"status": "ok"}


@app.get("/ready", tags=["Operations"], summary="Readiness check")
def ready():
    from sqlalchemy import text
    from app.database import SessionLocal

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}
