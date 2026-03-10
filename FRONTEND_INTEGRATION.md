# FRONTEND_INTEGRATION.md

This file defines the API contract for frontend integration (Lovable or any JS frontend).

## Base URLs

Local:
- `http://localhost:8001`

Example deployed:
- `https://your-backend-domain.example.com`

Use `API_BASE_URL` in frontend env config.

## Content Type

- Request: `Content-Type: application/json`
- Response: `application/json`

## Auth Header

Current mode:
- `AUTH_MODE=stub` (development)

Header is optional in stub mode:
```http
Authorization: Bearer user:my-dev-user-id
```

Future mode:
- `AUTH_MODE=supabase_jwt`
- Header will be required with Supabase access token.

## Standard Response Envelope

All endpoints return:

```json
{
  "success": true,
  "message": "Human-readable status",
  "data": {},
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 125,
    "total_pages": 7
  },
  "error": null
}
```

Error example:

```json
{
  "success": false,
  "message": "Request failed",
  "data": null,
  "pagination": null,
  "error": {
    "code": "HTTP_404",
    "detail": "Match not found"
  }
}
```

## Endpoints

## 1) Parse only

`POST /parse-log`

Request:
```json
{
  "player_name": "Neurologist2024",
  "raw_log": "Setup\nOpponent won the coin toss..."
}
```

Response data includes:
- `opponent_name`
- `winner`
- `went_first`
- `total_turns`
- `turns[]`
- `timeline_markdown`
- `prize_table_markdown`
- `competitive_summary_markdown`

## 2) Create/save match

`POST /matches`

Request:
```json
{
  "player_name": "Neurologist2024",
  "player_deck": "Teal Mask Ogerpon ex",
  "opponent_deck": "Raging Bolt ex",
  "raw_log": "Setup\n...",
  "notes": "optional"
}
```

Response data includes:
- `match_id`
- `result` (`win|loss|unknown`)
- `turn_count`, `prizes_taken`, `prize_diff`
- `turns[]`

## 3) List matches

`GET /matches?page=1&page_size=20&player_deck=...&opponent_deck=...&result=win`

Query params:
- `page` (default `1`)
- `page_size` (default `20`, max `200`)
- `player_deck` (optional)
- `opponent_deck` (optional)
- `result` (`win|loss|unknown`, optional)

Response data shape:
```json
{
  "items": [
    {
      "match_id": "...",
      "created_at": "2026-03-11T18:22:00Z",
      "player_name": "Neurologist2024",
      "opponent_name": "Rival123",
      "result": "win"
    }
  ]
}
```

`pagination` object is present for this endpoint.

## 4) Get one match

`GET /matches/{match_id}`

Returns full match payload including `turns` and `events`.

## 5) Stats

- `GET /stats/overview`
- `GET /stats/go-first`
- `GET /stats/by-deck`
- `GET /stats/by-matchup`

All stats endpoints return envelope with `data` payload and no pagination.

## 6) Health/version

- `GET /health`
- `GET /version`

Use these endpoints for frontend startup connectivity checks.

## Nullable Field Notes

Common nullable fields:
- `went_first` can be `null` when log does not contain first-player decision line.
- `player_deck`, `opponent_deck`, `summary_text` can be `null`.
- event fields like `damage`, `pokemon_involved` may be `null`.

## Frontend fetch examples

```ts
const res = await fetch(`${API_BASE_URL}/parse-log`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({ player_name, raw_log }),
});
const payload = await res.json();
if (!payload.success) throw new Error(payload.error?.detail ?? 'API error');
return payload.data;
```

```ts
const res = await fetch(`${API_BASE_URL}/matches?page=1&page_size=20`);
const payload = await res.json();
const items = payload.data.items;
const pagination = payload.pagination;
```

## Common errors

- `422 VALIDATION_ERROR` -> request schema invalid
- `404 HTTP_404` -> match id not found
- `501 HTTP_501` -> `AUTH_MODE=supabase_jwt` enabled but verification not implemented yet
