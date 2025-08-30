# Runbook

## Prerequisites
- Python 3.10+ (tested with 3.13)
- Node.js 18+ and npm

## Setup (once)
From the repo root:

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e "./fastapi[dev]"
```

Optional: set UI API base in `web/.env`:

```
VITE_API_BASE=http://localhost:8000
```

## Seed demo data
```
make seed
```

## Run backend (FastAPI)
```
make api
```
FastAPI runs on `http://localhost:8000`. Health: `GET /v1/health`.

## Run frontend (Vite)
In a second terminal:

```
cd web
npm install
npm run dev
```

Open the UI at: http://localhost:5173

## One-liner (both servers)
```
make dev
```

## Tests
```
cd fastapi
pytest -q
```

## Useful API endpoints
- `GET /v1/health`
- `GET /v1/balances`
- `GET /v1/suggestions`, `POST /v1/suggestions`
- `POST /v1/approvals/evaluate`
- `POST /v1/decisions`, `GET /v1/decisions`

