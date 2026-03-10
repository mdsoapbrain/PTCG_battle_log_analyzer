# README_backend.md

Backend is now frontend-consumable and deployment-ready for Lovable integration.

## Architecture

```text
backend/
  main.py
  api/
    routes_parse.py
    routes_matches.py
    routes_stats.py
  core/
    parser.py
    battle_summary.py
    stats.py
    models.py
    schemas.py
    database.py
    config.py
    auth_stub.py
  services/
    match_service.py
    stats_service.py
  repositories/
    match_repository.py
  demo_assets/
    sample_raw_log.txt
  utils/
    responses.py
alembic/
  env.py
  versions/
scripts/
  seed_demo_matches.py
tests/
```

Parser logic is preserved in Python (`backend/core/parser.py`) and not rewritten to TypeScript.

## Environment variables

Copy and edit:

```bash
cp .env.example .env
```

Supported env vars:
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `APP_NAME`
- `APP_VERSION`
- `API_PREFIX`
- `DATABASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `API_BASE_URL`
- `SECRET_KEY`
- `AUTH_MODE` (`stub` or `supabase_jwt`)

Local SQLite default:
- `DATABASE_URL=sqlite:///./backend.db`

Future Postgres/Supabase example:
- `DATABASE_URL=postgresql+psycopg://postgres:password@host:5432/dbname`

## Local development

### 1) Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 2) Run API

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

### 3) Verify

- Health: `GET http://localhost:8001/health`
- Version: `GET http://localhost:8001/version`
- Docs: `http://localhost:8001/docs`

## Docker deployment

### Build and run

```bash
docker build -t ptcg-backend .
docker run --env-file .env -p 8001:8001 ptcg-backend
```

### Compose (local dev)

```bash
docker compose up --build
```

## Render deployment (quick path)

1. Open Render Dashboard -> `New` -> `Blueprint`
2. Connect this GitHub repo
3. Render will detect [`render.yaml`](/Users/danny/Desktop/pokemon_calculator/ptcg-consistency/render.yaml)
4. Set `API_BASE_URL` and `CORS_ALLOWED_ORIGINS` in the Render UI
5. Deploy

## API contract

All endpoints return a standard envelope:

```json
{
  "success": true,
  "message": "...",
  "data": {},
  "pagination": null,
  "error": null
}
```

Paginated endpoints include `pagination` object.

Endpoints:
- `POST /parse-log`
- `POST /matches`
- `GET /matches`
- `GET /matches/{match_id}`
- `GET /stats/overview`
- `GET /stats/go-first`
- `GET /stats/by-deck`
- `GET /stats/by-matchup`
- `GET /health`
- `GET /version`

Detailed frontend contract: see [`FRONTEND_INTEGRATION.md`](/Users/danny/Desktop/pokemon_calculator/ptcg-consistency/FRONTEND_INTEGRATION.md).

## CORS

CORS is enabled in FastAPI middleware and configured by:
- `CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://your-lovable-frontend.example.com`

## Auth mode

Current implementation (`backend/core/auth_stub.py`):
- `AUTH_MODE=stub`: optional bearer token, dev user returned
- `AUTH_MODE=supabase_jwt`: token required, verification is TODO (explicit not implemented)

Supabase integration hook is already isolated there.

## Alembic migrations

Scaffold added:
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/0001_initial_schema.py`

Commands:

```bash
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

## Seed/demo data

- Sample battle log: [`backend/demo_assets/sample_raw_log.txt`](/Users/danny/Desktop/pokemon_calculator/ptcg-consistency/backend/demo_assets/sample_raw_log.txt)
- Seed script:

```bash
python scripts/seed_demo_matches.py
```

## Tests

```bash
python3.11 -m pytest -q
```

Included:
- parser smoke
- API endpoint
- stats
- DB insert
- health/version

## Migration note for Supabase Postgres

When moving to Supabase:
1. Set `DATABASE_URL` to Supabase Postgres connection string.
2. Run `alembic upgrade head` in target environment.
3. Replace `AUTH_MODE=stub` with `AUTH_MODE=supabase_jwt` after implementing JWT verification in `auth_stub.py`.
4. Keep API contract unchanged for frontend continuity.
