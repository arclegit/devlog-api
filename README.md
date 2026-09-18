#DevLog Api

REST API to log coding sessions and get analytics on your dev time.

Built with FastAPI + PostgreSQL as a backend engineering project.

##What it does

- **Auth:** Register, login with JWT, `/auth/me`
- **Sessions:** CRUD for coding sessions. Active sessions have `ended_at = null`. Users can only see their own sessions.
- **Analytics:** Summary, by language, by project, daily, weekly. Duration is computed as `ended_at - started_at`, not stored.

##Stack

Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL + psycopg, Alembic, PyJWT + pwdlib, Uvicorn, pytest + HTTPX

##Structure

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
alembic/          # migrations
tests/            # pytest, sqlite in-memory
docs/
  http://database-design.md

##Setup

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
Auth via `Authorization: Bearer <token>`

Testing

Tests use SQLite in-memory, prod uses PostgreSQL.
pytest -q
53 passed
Notes

- Passwords are hashed, never stored plain
- Active sessions are excluded from duration-based analytics
- Analytics use DB-side aggregation (COUNT, SUM, AVG, GROUP BY)

---

Documentation assisted by AI, reviewed and edited by me.