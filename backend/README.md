# AssignmentBridge backend

The backend is a FastAPI service that collects upcoming assignments from
Canvas LMS and Gradescope. It filters records to the configured future window,
keeps them in an in-memory cache, and exposes the cache and server state under
`/api`.

## Responsibilities

- Run the FastAPI application with Uvicorn on port `8081`.
- Refresh assignments once at startup and periodically thereafter.
- Fetch Canvas assignments through the Canvas GraphQL API.
- Fetch Gradescope assignments through Playwright browser automation.
- Combine enabled integrations into one cached list.
- Publish refresh status to connected frontend clients using SSE.
- Persist ordinary settings in SQLite and secrets in the OS keyring.
- Optionally create an ngrok tunnel for the local server.

## Requirements

- Python 3.10 or newer.
- A Python keyring backend supported by the host operating system.
- Playwright Chromium for Gradescope automation.
- Canvas credentials and/or Gradescope credentials, depending on the enabled
  integrations.

## Installation

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .
python -m playwright install chromium
```

The project metadata is in [`pyproject.toml`](./pyproject.toml). Dependencies
include FastAPI, Uvicorn, Pydantic (through FastAPI), `sse-starlette`,
`keyring`, `ngrok`, `python-dotenv`, and Playwright.

## Run the server

The source uses a `src/` layout and is not packaged with an installed console
script. Start it from `backend/` with:

```bash
PYTHONPATH=src python -m server
```

The server is available at `http://localhost:8081`. It initializes the
settings database and performs an initial refresh during startup. Stop it with
`Ctrl+C`.

For direct integration checks, after configuring credentials:

```bash
PYTHONPATH=src python -m canvas.client
PYTHONPATH=src python -m gradescope.client
```

## Configuration

Configuration is managed through the frontend's Server Settings form or
through the backend API. The available values are:

| Group | Settings |
| --- | --- |
| General | `refresh_interval` (seconds), `weeks_delta` |
| Canvas | enabled flag, GraphQL URL, access token |
| Gradescope | enabled flag, email, password |
| ngrok | enabled flag, domain, authtoken |

Defaults are:

- `refresh_interval`: `3600` seconds
- `weeks_delta`: `10`
- Canvas, Gradescope, and ngrok: disabled

The SQLite database is created at
`backend/src/config/settings.db`. Sensitive values are stored using the
`AssignmentBridge` keyring service instead of SQLite. Gradescope login state
is saved to `backend/src/gradescope/auth.json` for reuse by Playwright. These
files are local state and must not be committed or shared.

## API

All routes are prefixed with `/api`:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/status` | Return health, cache size, refresh state, and last error |
| `GET` | `/settings` | Return settings without secret values |
| `POST` | `/settings` | Partially update settings |
| `GET` | `/assignments` | Return cached filtered assignments |
| `POST` | `/refresh` | Start a background refresh |
| `GET` | `/events` | Stream `server_status` SSE events |

`POST /settings` accepts any subset of the settings fields. The response is
`{"status": "ok"}`. `POST /refresh` responds with
`{"status": "refresh_started"}` while the work continues in the background.

Assignments are returned as dictionaries with:

```json
{
  "course": "MATH 1",
  "assignment": "Homework",
  "dueAt": "2026-09-20T23:59:00+00:00"
}
```

## Refresh behavior

At startup and on each scheduled refresh, the service:

1. Loads the current settings.
2. Queries each enabled and configured integration.
3. Filters assignments from now through `weeks_delta` weeks in the future.
4. Replaces the in-memory cache and records the refresh timestamp.
5. Publishes the new status to SSE subscribers.

An integration failure is recorded in `last_refresh_error`, while successfully
retrieved assignments from other enabled integrations remain available.

## Security and deployment notes

The default server uses unauthenticated HTTP and is intended for local use.
ngrok is optional and should only be enabled when the tunnel domain and token
are controlled by the operator. The service has no user authentication layer,
so exposing it beyond a trusted local network requires an external access
control and TLS strategy.
