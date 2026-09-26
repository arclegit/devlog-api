import os

from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set")


ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

AI_API_KEY = os.getenv("AI_API_KEY") or os.getenv("GEMINI_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")
AI_TIMEOUT_SECONDS = float(
    os.getenv("AI_TIMEOUT_SECONDS", "30")
)
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock")

AI_STREAMING_ENABLED = os.getenv("AI_STREAMING_ENABLED", "false").lower() == "true"
AI_TOKEN_USAGE_TRACKING_ENABLED = os.getenv("AI_TOKEN_USAGE_TRACKING_ENABLED", "false").lower() == "true"
AI_COST_LOGGING_ENABLED = os.getenv("AI_COST_LOGGING_ENABLED", "false").lower() == "true"
AI_BASE_URL = os.getenv(
    "AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "mock")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))