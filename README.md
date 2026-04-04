# PTCG Battle Log Analyzer (Backend + Frontend)

This repository now contains both:

- `backend/` FastAPI API (parser, storage, stats)
- `frontend/` React + Vite web app (dashboard, parse/save UI)

Parser/business logic remains in Python.

Important:
- Local dev can use SQLite.
- Production should use Postgres/Supabase Postgres.
- Render Docker + SQLite does not keep data after restart or redeploy.

## Repo Structure

```text
backend/      # FastAPI app
frontend/     # React app
alembic/      # DB migrations
scripts/      # seed/demo scripts
tests/        # backend tests
app.py        # legacy Streamlit app (optional)
```

## Quick Start (Clone and run)

```bash
git clone https://github.com/mdsoapbrain/PTCG_battle_log_analyzer.git
cd PTCG_battle_log_analyzer
```

### 1) Run backend

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

Backend docs:
- [http://localhost:8001/docs](http://localhost:8001/docs)

If you want the same startup flow used in production:

```bash
./scripts/start_backend.sh
```

### 2) Run frontend

Open a second terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend URL:
- [http://localhost:8080](http://localhost:8080)

## Production URLs (current)

- API base: [https://ptcg-backend-7jos.onrender.com](https://ptcg-backend-7jos.onrender.com)
- Docs: [https://ptcg-backend-7jos.onrender.com/docs](https://ptcg-backend-7jos.onrender.com/docs)
- OpenAPI: [https://ptcg-backend-7jos.onrender.com/openapi.json](https://ptcg-backend-7jos.onrender.com/openapi.json)

## Persistent Production Database

To keep match history after redeploys, set `DATABASE_URL` in Render to a Postgres connection string.

Supabase example:

```bash
DATABASE_URL=postgresql://postgres:password@db-host:5432/postgres
```

The backend automatically normalizes this to the correct SQLAlchemy driver form and runs migrations on startup.

If your Render service already exists, update `DATABASE_URL` manually in the Render Dashboard. The Blueprint now marks it as `sync: false`, so future syncs will not replace that value for you.

## Frontend/Backend Contract

- Contract doc: [FRONTEND_INTEGRATION.md](/Users/danny/Desktop/pokemon_calculator/ptcg-consistency/FRONTEND_INTEGRATION.md)
- Backend run/deploy doc: [README_backend.md](/Users/danny/Desktop/pokemon_calculator/ptcg-consistency/README_backend.md)

## Auth (current)

- `AUTH_MODE=stub`
- Bearer token is optional
- Dev token format recommended: `Authorization: Bearer user:<id>`

## Legacy Streamlit (optional)

If you still want the single-file Streamlit version:

```bash
streamlit run app.py
```
