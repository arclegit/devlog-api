# DevLog API

Developer activity logging and analytics REST API built with FastAPI.

DevLog allows authenticated developers to record coding sessions and view
activity analytics based on their development history.

## Current Status

The current version includes:

- User registration
- JWT authentication
- Current-user authentication
- Coding session CRUD
- Session ownership enforcement
- Active coding sessions
- Session validation
- Pagination
- Developer activity analytics
- Automated API tests
- PostgreSQL database
- SQLAlchemy ORM
- Alembic migrations
- FastAPI OpenAPI documentation


## Tech Stack

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT / PyJWT
- pwdlib
- pytest
- HTTPX
- Uvicorn


## Project Structure

devlog-api/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── README
│
├── app/
│   ├── analytics.py
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── sessions.py
│
├── docs/
│   └── database-design.md
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_validation.py
│
├── .env
├── .gitignore
├── alembic.ini
├── README.md
└── requirements.txt