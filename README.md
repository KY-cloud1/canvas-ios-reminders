# AssignmentBridge

AssignmentBridge is a local assignment aggregator for Canvas LMS and
Gradescope. The project contains:

- A FastAPI backend that retrieves assignments, filters them by due date, and
  keeps a refreshed in-memory cache.
- A React and Vite frontend for viewing server health, editing integration
  settings, and triggering a refresh.
- Optional ngrok tunneling for reaching the local API from another device.

The backend stores ordinary settings in SQLite and stores credentials in the
operating system keyring. Credentials are not returned by the settings API.

## Repository layout

```text
backend/
  src/
    canvas/       Canvas GraphQL client and date filtering
    config/       SQLite settings and keyring-backed secrets
    gradescope/   Playwright-based Gradescope client
    schemas/      FastAPI/Pydantic request models
    server.py     FastAPI application and refresh lifecycle
frontend/
  src/
    api/          Backend API calls
    components/   Settings, status, and refresh UI
    context/      Server-sent event (SSE) status state
    hooks/        React settings state management
    types/        Frontend API types
```

## Requirements

- Python 3.10 or newer (the project is developed with Python 3.13).
- Node.js and pnpm.
- A Canvas GraphQL endpoint and access token if Canvas is enabled.
- A Gradescope account if Gradescope is enabled.
- Chromium installed by Playwright if Gradescope is enabled.

## Quick start

Open two terminals from the repository root.

### 1. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .
python -m playwright install chromium
PYTHONPATH=src python -m server
```

The API listens on `http://localhost:8081`.

### 2. Start the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open the URL printed by Vite, normally `http://localhost:5173`. During
development, Vite proxies `/api` requests to the backend at
`http://localhost:8081`.

The backend performs an initial refresh during startup. With both integrations
disabled, it starts with an empty assignment cache; configure at least one
integration in the frontend before refreshing.

## Configuration

Use the **Server Settings** panel in the frontend to configure:

- **General**: refresh interval in seconds and the number of future weeks to
  include.
- **Canvas**: enabled state, Canvas GraphQL URL, and access token.
- **Gradescope**: enabled state, email, and password.
- **ngrok**: enabled state, reserved domain, and authtoken.

The defaults are a 60-minute refresh interval, a 10-week assignment window,
and all integrations disabled. Non-sensitive settings are stored in
`backend/src/config/settings.db`. Canvas tokens, Gradescope credentials, and
the ngrok authtoken are stored through the `AssignmentBridge` keyring service.
Do not commit `settings.db`, `auth.json`, or credentials.

## Development commands

Frontend commands are run from `frontend/`:

```bash
pnpm dev       # Start the Vite development server
pnpm build     # Type-check and create a production build
pnpm lint      # Run ESLint
pnpm preview   # Preview the production build
```

The backend has no separate test suite or CLI wrapper yet. Its modules can be
run directly with `PYTHONPATH=src`, for example:

```bash
PYTHONPATH=src python -m canvas.client
PYTHONPATH=src python -m gradescope.client
```

These integration entry points require the corresponding credentials to be
configured first.

## Security and network notes

- The default server is HTTP on localhost. It does not provide TLS itself.
- ngrok is optional and should only be enabled with a domain and authtoken
  that you control.
- Canvas and Gradescope credentials are used locally for API requests and
  browser automation. Treat the generated Gradescope browser state file as
  sensitive.
- If the API is made reachable from another device, protect the network and
  endpoint appropriately; the application does not implement user
  authentication.

## API overview

The backend mounts its routes under `/api`:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/status` | Current health, cache size, refresh state, and last error |
| `GET` | `/api/settings` | Non-secret configuration and credential-configured flags |
| `POST` | `/api/settings` | Partially update configuration |
| `GET` | `/api/assignments` | Return cached upcoming assignments |
| `POST` | `/api/refresh` | Schedule a background assignment refresh |
| `GET` | `/api/events` | Stream status updates over server-sent events |

Assignment records use the shape `course`, `assignment`, and `dueAt`.
