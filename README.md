# watermelon-backend

FastAPI backend for the watermelon project.

## Project Structure

```text
watermelon-backend/
├── src/
│   └── app/
│       ├── api/
│       │   └── v1/
│       │       ├── endpoints/
│       │       │   ├── database.py
│       │       │   ├── health.py
│       │       │   └── prices.py
│       │       └── router.py
│       ├── core/
│       │   └── config.py
│       ├── db/
│       │   ├── base.py
│       │   └── session.py
│       ├── schema/
│       │   ├── health.py
│       │   └── price.py
│       └── main.py
├── tests/
│   └── test_health.py
├── .env.example
└── pyproject.toml
```

## Setup

```bash
cd /Users/cosmic/python/ms-study/project/watermelon-backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` for your local PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/watermelon
```

## Run

```bash
uvicorn app.main:app --reload --app-dir src
```

Open:

- API root: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/api/v1/health
- Database ping: http://127.0.0.1:8000/api/v1/database/ping
- Weekly prices: http://127.0.0.1:8000/api/v1/prices?date=2026-06-22
- Swagger UI: http://127.0.0.1:8000/docs

## Test

```bash
pytest
```

## Local PostgreSQL (Docker)

```bash
docker compose up -d db
```

This starts only PostgreSQL (`watermelon` DB, `postgres`/`postgres` credentials) on
`localhost:5432`, matching `DATABASE_URL` in `.env.example`. The API, data pipeline,
and dashboard live in separate repos/services and will be integrated later.
