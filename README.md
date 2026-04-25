# NEWSRADAR

Sistema de monitorización de noticias — UC3M Desarrollo y Operación de Sistemas Software.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.11 |
| Frontend | React 19 + Vite |
| Database | PostgreSQL 15 + SQLAlchemy 2.0 (sync) |
| Search | Elasticsearch 8.12 |
| Deployment | Docker / Docker Compose |
| CI/CD | GitHub Actions |

## Quick Start

```bash
# Start databases
cd Backend && docker compose up -d

# Start backend
cd Backend && pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# Start frontend
cd Frontend && npm install && npm run dev
```

Backend: http://localhost:8000 | Frontend: http://localhost:5173 | API Docs: http://localhost:8000/docs

## Development

### Quality Checks

```bash
make lint          # Ruff lint
make format-check  # Ruff format check
make typecheck     # Ty type check
make check         # Lint + typecheck + unit tests (quick)
make ci            # Full CI pipeline locally
```

### Testing

```bash
make test-unit           # Backend unit tests
make test-integration    # Backend integration tests (needs PostgreSQL)
make test-frontend       # Frontend Vitest tests
make test-e2e            # E2E Playwright tests
make coverage            # Backend tests with coverage report
```

See [docs/development/testing.md](docs/development/testing.md) for full details.

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## CI/CD

GitHub Actions runs on every push to `main` and on pull requests:

- **Backend:** Ruff lint, Ty type check, pytest unit + integration tests
- **Frontend:** Vitest tests, build check
- **E2E:** Playwright smoke + auth tests
- **Security:** pip-audit, npm audit, Trivy container scan
- **Quality:** SonarQube analysis
- **Docs:** MkDocs build (PR) + deploy a GitHub Pages (main)

See [docs/deployment/cicd.md](docs/deployment/cicd.md) for full pipeline details.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/build.sh` | Build Docker images |
| `scripts/test.sh` | Run all tests |
| `scripts/test-backend.sh` | Backend tests only |
| `scripts/test-frontend.sh` | Frontend tests only |
| `scripts/test-e2e.sh` | E2E tests (auto-starts services) |
| `scripts/deploy.sh` | Build + deploy with Docker Compose |
| `scripts/check.sh` | Quick lint + typecheck + unit tests |
| `scripts/ci-local.sh` | Full CI pipeline locally |
| `scripts/gen-docs.sh` | Export OpenAPI documentation |

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system architecture, data model, and C4 diagrams.

## ADRs

Architecture decisions are documented in [docs/adr/](docs/adr/):

| ADR | Decision |
|---|---|
| [0001](docs/adr/0001-framework-backend-fastapi.md) | Framework backend: FastAPI + Pydantic V2 |
| [0002](docs/adr/0002-autenticacion-jwt.md) | Autenticación: JWT stateless |
| [0003](docs/adr/0003-verificacion-email-smtplib-mailtrap.md) | Email: smtplib + Mailtrap |
| [0004](docs/adr/0004-persistencia-postgresql.md) | Persistencia: PostgreSQL 15 + SQLAlchemy 2.0 síncrono |
| [0005](docs/adr/0005-frontend-react-vite.md) | Frontend: React 19 + Vite |
| [0006](docs/adr/0006-elasticsearch-indexacion-noticias.md) | Búsqueda: Elasticsearch 8.12 |
| [0007](docs/adr/0007-frontend-bootstrap-react-router.md) | UI: Bootstrap 5 + React Router |
| [0008](docs/adr/0008-calidad-codigo-ruff-ty.md) | Calidad: Ruff + Ty |
| [0009](docs/adr/0009-estrategia-testing-pytest-vitest-playwright.md) | Testing: Pytest + Vitest + Playwright |
| [0010](docs/adr/0010-migraciones-bd-alembic.md) | Migraciones: Alembic |
| [0011](docs/adr/0011-pipeline-cicd-github-actions.md) | CI/CD: GitHub Actions |
| [0012](docs/adr/0012-seguridad-scanning-pip-audit-trivy-sonarqube.md) | Seguridad: pip-audit + Trivy + SonarQube |
| [0013](docs/adr/0013-documentacion-backend-mkdocs-docstrings.md) | Documentación backend: docstrings + MkDocs |
| [0014](docs/adr/0014-integracion-api-gestion-fuentes-alertas.md) | Frontend ↔ API: capa de servicios + JWT en localStorage |
