DevLog Api

[![CI](https://github.com/arclegit/devlog-api/actions/workflows/ci.yml/badge.svg)](https://github.com/arclegit/devlog-api/actions/workflows/ci.yml)
![Coverage gate](https://img.shields.io/badge/coverage-%E2%89%A580%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

REST API to log coding sessions and get analytics on your dev time.

Built with FastAPI + PostgreSQL as a backend engineering project.

What it does

- **Auth:** Register, login with JWT, `/auth/me`
- **Account lifecycle:** Password change, soft account deletion, and a validated IANA timezone preference.
- **Sessions:** CRUD for coding sessions. Active sessions have `ended_at = null`. Users can only see their own sessions.
- **Analytics:** Summary, by language, by project, daily, weekly, with `from` / `to` filters. Duration is computed as `ended_at - started_at`, not stored.
- **AI summaries:** `POST /ai/activity-summary` generates an interpretation of your activity for a date range. Analytics are computed by the app; the AI provider only writes the summary. Mock and OpenAI providers, provider failure mapping, and a 5/minute rate limit.
- **Operations:** JSON structured request logs, request IDs, rate-limited authentication, and `/health` / `/ready` probes.

Stack

Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL + psycopg, Alembic, PyJWT + pwdlib, OpenAI (optional AI provider), Uvicorn, pytest + HTTPX

Structure

app/
  http://main.py         # app factory & routers
  http://models.py       # User, CodingSession
  http://schemas.py      # Pydantic schemas
  http://database.py     # engine, session
  http://config.py       # env config
  http://auth.py         # register/login/me
  http://sessions.py     # session CRUD
  http://analytics.py    # aggregated queries
  http://security.py     # hashing, JWT
  http://dependencies.py # get_current_user, get_db
  ai/               # AI provider boundary, service, context, router
alembic/          # migrations
tests/            # pytest, sqlite in-memory
docs/
  http://database-design.md

Setup

```bash
git clone https://github.com/arclegit/devlog-api.git
cd devlog-api

venv
python -m venv .venv
windows
.venv\Scripts\Activate.ps1
mac/linux
source .venv/bin/activate

pip install -r requirements.txt
Env

Create `.env` from `.env.example`:
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/devlog
JWT_SECRET_KEY=your-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI activity summaries
AI_PROVIDER=mock            # mock | openai
AI_API_KEY=                 # required when AI_PROVIDER=openai
AI_MODEL=gemini-2.5-flash
AI_TIMEOUT_SECONDS=30
RATE_LIMIT_ENABLED=true
`.env` is gitignored. Never commit it.

Database
alembic upgrade head
alembic current
Schema is managed only by Alembic. See `docs/database-design.md` for model decisions (why email is NOT NULL + UNIQUE, why duration is derived).

Run
uvicorn app.main:app --reload
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Endpoints
POST /auth/register
POST /auth/login
GET  /auth/me
POST /auth/change-password
DELETE /auth/me

POST   /sessions/
GET    /sessions/
GET    /sessions/{id}
PATCH  /sessions/{id}
DELETE /sessions/{id}

GET /analytics/summary
GET /analytics/languages
GET /analytics/projects
GET /analytics/daily
GET /analytics/weekly

POST /ai/activity-summary
Auth via `Authorization: Bearer <token>`

All errors share the form `{"error": {"code", "message", "request_id", "details?"}}`. Send `X-Request-ID` to provide your own correlation ID, or read the one returned in every response.

Analytics can be scoped with ISO 8601 timestamps, for example: `GET /analytics/summary?from=2026-01-01T00:00:00Z&to=2026-01-31T23:59:59Z`.

AI activity summary

`POST /ai/activity-summary` requires a Bearer token and is limited to 5 requests per minute.

Request:

```json
{
  "start_date": "2026-09-01",
  "end_date": "2026-09-20"
}
```

Response `200`:

```json
{
  "summary": "Development activity was recorded across 12 completed sessions.",
  "focus_areas": ["Python", "SQL"],
  "patterns": ["12 completed coding sessions were recorded during the selected period."]
}
```

Behavior:

- The app computes all analytics (sessions, durations, languages, projects, daily activity) from your own data and passes them to the provider as structured context. The AI never calculates statistics.
- The provider is selected with `AI_PROVIDER` (`mock` or `openai`). `mock` is the default and needs no API key; `openai` requires `AI_API_KEY` and uses `AI_MODEL` / `AI_TIMEOUT_SECONDS`.
- Provider failures map to: `504` timeout, `503` provider rate limit / not configured, `502` provider API error or invalid structured response. All errors use the standard error envelope and include the request ID.
- Only completed sessions (with `ended_at`) in the requested date range are included.

Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. The API container runs Alembic migrations before starting. The compose credentials are development-only; set real environment secrets for deployment.

Testing

Tests use SQLite in-memory, prod uses PostgreSQL.
pytest -q
74 passed

CI runs the suite with coverage and enforces an 80% minimum. The workflow is in `.github/workflows/ci.yml`.
Notes

- Passwords are hashed, never stored plain
- Active sessions are excluded from duration-based analytics
- Analytics use DB-side aggregation (COUNT, SUM, AVG, GROUP BY)

---

Documentation assisted by AI, reviewed and edited by me.
