# PTCG Frontend (React + Vite)

This frontend is maintained in this repo (not Lovable-dependent).
It connects to the FastAPI backend in `../backend`.

## Requirements

- Node.js 18+
- npm

## Setup

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Default dev URL: [http://localhost:8080](http://localhost:8080)

## Environment

`VITE_API_BASE_URL` is required to point to your backend.

Examples:
- local: `http://localhost:8001`
- deployed: `https://ptcg-backend-7jos.onrender.com`

## Build

```bash
npm run build
npm run preview
```

## Current pages

- Dashboard
- Parse Log
- Match History
- Match Detail
- Deck Analytics
- Matchup Analytics
- Settings

All pages use the backend response envelope:

```json
{
  "success": true,
  "message": "ok",
  "data": {},
  "pagination": null,
  "error": null
}
```
