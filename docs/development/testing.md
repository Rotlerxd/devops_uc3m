# Testing Strategy — NEWSRADAR

- **Versión:** 1.0
- **Fecha:** 2026-03-25

---

## Overview

NEWSRADAR follows a test pyramid approach with three layers:

| Layer | Framework | Scope | Run command |
|---|---|---|---|
| Backend unit | pytest + pytest-asyncio | Isolated logic, schemas, security | `make test-unit` |
| Backend integration | pytest + httpx | API endpoints, DB, auth flow | `make test-integration` |
| Frontend unit | Vitest + Testing Library | React components, pages | `make test-frontend` |
| E2E | Playwright | Full-stack user flows | `make test-e2e` |

---

## Backend Tests

### Structure

```
Backend/tests/
├── conftest.py              # env vars, shared fixtures
├── unit/
│   ├── test_security.py     # password hashing, JWT tokens
│   ├── test_schemas.py      # Pydantic validation
│   └── test_crud_usuario.py # CRUD with mocked DB
└── functional/
    ├── conftest.py           # real PostgreSQL fixtures, test client
    ├── test_auth.py          # /login, /register, /me endpoints
    └── test_health.py        # /health endpoint
```

### Running

```bash
# Unit tests only (no external services needed)
cd Backend && pytest tests/unit -m unit

# Integration tests (requires PostgreSQL + Elasticsearch)
cd Backend && docker compose up -d
cd Backend && alembic upgrade head
cd Backend && pytest tests/functional -m integration

# All tests with coverage
cd Backend && pytest tests/ --cov=app --cov-report=term-missing
```

### Markers

- `@pytest.mark.unit` — isolated, no DB/network
- `@pytest.mark.integration` — requires PostgreSQL + Elasticsearch
- `@pytest.mark.functional` — legacy alias kept for older backend tests
- `@pytest.mark.e2e` — reserved for Playwright (run separately)

### Async Testing

All backend tests use `pytest-asyncio` with `asyncio_mode = "auto"` (configured in `pyproject.toml`). Just write `async def test_...` and it works.

---

## Frontend Tests

### Structure

```
Frontend/src/test/
├── setup.js               # jest-dom matchers
├── Login.test.jsx         # Login page rendering
└── Register.test.jsx      # Register page rendering
```

### Running

```bash
cd Frontend
npm run test:run           # single run
npm run test               # watch mode
npm run test:coverage      # with coverage
```

---

## E2E Tests

### Structure

```
e2e/
├── playwright.config.js
└── tests/
    ├── smoke.spec.js      # app loads, pages render
    └── auth.spec.js       # login/register navigation, form fields
```

### Running

```bash
# Requires backend + frontend running
cd Backend && uvicorn app.main:app --port 8000 &
cd Frontend && npm run dev &
cd e2e && npx playwright test
```

Or use the script: `scripts/test-e2e.sh` (starts services automatically).

---

## Coverage

- Backend threshold: **60%** (configured in `pyproject.toml`)
- Coverage reports generated as `htmlcov/` in Backend directory
- CI uploads coverage to SonarQube for trending

---

## Adding New Tests

1. **Backend unit test:** Create `test_<feature>.py` in `Backend/tests/unit/`. Use `@pytest.mark.unit`.
2. **Backend integration test:** Create `test_<feature>.py` in `Backend/tests/functional/`. Use `@pytest.mark.integration`. Fixtures in `conftest.py` provide a test DB session and HTTP client.
3. **Frontend test:** Create `<Component>.test.jsx` co-located or in `Frontend/src/test/`.
4. **E2E test:** Create `<flow>.spec.js` in `e2e/tests/`.
