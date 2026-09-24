# AssignmentBridge frontend

The frontend is a React 19 single-page application built with TypeScript and
Vite. It provides a local dashboard for the AssignmentBridge FastAPI backend.

## What it does

- Shows backend health, cached assignment count, refresh time, and refresh
  errors.
- Receives live refresh state through a server-sent events connection at
  `/api/events`.
- Reads and updates general, Canvas, Gradescope, and ngrok settings.
- Triggers an on-demand assignment refresh and disables the button while the
  backend is refreshing.

The application is composed around `App`, `ServerProvider`, and three main
dashboard components:

```text
src/
  api/server.ts                         Backend requests
  components/ServerStatusPanel/         Live server status
  components/ServerSettingsPanel/       Settings form
  components/SeverRefreshButton/         Manual refresh control
  context/ServerContext.tsx              Shared SSE status state
  hooks/useServerSettings.ts             Settings loading and saving
  types/server.ts                        API response and request types
```

## Requirements

- Node.js
- pnpm
- The AssignmentBridge backend running on port `9101` for live data

## Install and run

From this directory:

```bash
pnpm install
pnpm dev
```

Vite prints the local development URL, normally `http://localhost:5173`.
Requests to `/api` are proxied to `http://localhost:9101` by
[`vite.config.ts`](./vite.config.ts), so start the backend separately when
using the dashboard.

To preview the production bundle as served by FastAPI instead of the Vite dev
server, run:

```bash
pnpm build
```

Then start the backend from `backend/` with `PYTHONPATH=src python -m server`.
The backend serves the app at `http://localhost:9101` and serves the assets
from `/assets`.

## Commands

```bash
pnpm dev       # Start Vite with hot module replacement
pnpm build     # Type-check with tsc and build the dist/ directory
pnpm lint      # Run ESLint
pnpm preview   # Serve the built dist/ directory locally
```

## Backend contract

The frontend expects these backend routes:

- `GET /api/status`
- `GET /api/settings`
- `POST /api/settings`
- `POST /api/refresh`
- `GET /api/events` (SSE event name: `server_status`)

The frontend does not store credentials. Password and token inputs are sent
only when a new value is entered; configured credentials are represented by
boolean flags returned by the backend.

## Production build

Run `pnpm build` to create a static production bundle in `dist/`. The backend
serves that build directly at `/` and `/assets`, so the app can be opened from
`http://localhost:9101` without a separate frontend web server. For non-local
hosting, configure the reverse proxy to route `/api` and `/api/events` to the
FastAPI service while serving the static app bundle from the backend.
