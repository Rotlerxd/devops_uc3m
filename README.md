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
cd Backend && pip install -r requirements-dev.txt
cd Backend && alembic upgrade head
python -m uvicorn app.main:app --reload

# Start frontend
cd Frontend && npm install && npm run dev
```

Backend: http://localhost:8000 | Frontend: http://localhost:5173 | API Docs: http://localhost:8000/docs

## Development

### Local fastText Synonym Fallback

The Spanish synonym feature can optionally use local fastText vectors for
related-term suggestions when WordNet has low coverage. This path is
**experimental**: fastText returns semantically related terms, not guaranteed
strict synonyms, and it should not be enabled for normal production deployments
unless the team has validated the model quality and memory footprint for that
environment. It is available for local evaluation or deployments that explicitly
want to try broader vocabulary coverage.

Use the binary model (`.bin`), not the text vectors file (`.vec`).

```bash
# Download Spanish fastText vectors to .models/fasttext/cc.es.300.bin
scripts/download-fasttext-es.sh

# Start backend + frontend with the optional fastText fallback enabled
scripts/start-dev.sh --both-parallel --fasttext

# Or use a custom binary model path
scripts/start-dev.sh --both-parallel --fasttext-model /path/to/cc.es.300.bin
```

The model file is local-only and is not committed to the repository.

### Synonym Generation for Alerts

When creating or editing alerts, the system can automatically generate synonyms for descriptor terms to improve search coverage. This feature uses NLTK WordNet with the Open Multilingual WordNet (OMW) corpus for Spanish synonym generation, with an optional local fastText fallback for broader vocabulary coverage.

The backend exposes two endpoints:
- `GET /api/v1/alerts/synonyms?term=<termino>&limit=<3-10>` - generates synonyms for a term
- `GET /api/v1/alerts/synonyms/warmup` - preloads NLTK resources to reduce first-request latency

In the frontend alert creation modal, synonyms appear as clickable chips below each descriptor field. Users can add suggested synonyms to their alert descriptors (maintaining the 3-10 term limit per alert).

The fastText fallback remains **experimental** and is disabled by default. To enable it locally:
1. Download Spanish fastText vectors: `scripts/download-fasttext-es.sh`
2. Start services with: `scripts/start-dev.sh --both-parallel --fasttext`

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
| `scripts/download-fasttext-es.sh` | Download optional Spanish fastText vectors |

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full system architecture, data model, and C4 diagrams.

## ADRs

Architecture decisions are documented in [docs/adr/](docs/adr/):

| ADR | Decision |
|---|---|
| [0001](docs/adr/0001-framework-backend-fastapi.md) | Framework backend: FastAPI + Pydantic V2 |
| [0002](docs/adr/0002-autenticacion-jwt.md) | Autenticación: JWT stateless |
| [0003](docs/adr/0003-verificacion-email-smtplib-mailtrap.md) | Email: smtplib + Mailtrap |
| [0004](docs/adr/0004-persistencia-en-memoria.md) | Persistencia en memoria (histórico, supersedido por ADR 0015) |
| [0005](docs/adr/0005-frontend-react-vite.md) | Frontend: React 19 + Vite |
| [0006](docs/adr/0006-elasticsearch-indexacion-noticias.md) | Búsqueda: Elasticsearch 8.12 |
| [0007](docs/adr/0007-frontend-bootstrap-react-router.md) | UI: Bootstrap 5 + React Router |
| [0008](docs/adr/0008-calidad-codigo-ruff-ty.md) | Calidad: Ruff + Ty |
| [0009](docs/adr/0009-estrategia-testing-pytest-vitest-playwright.md) | Testing: Pytest + Vitest + Playwright |
| [0010](docs/adr/0010-migraciones-bd-alembic.md) | Migraciones: Alembic |
| [0011](docs/adr/0011-pipeline-cicd-github-actions.md) | CI/CD: GitHub Actions |
| [0012](docs/adr/0012-seguridad-scanning-pip-audit-trivy-sonarqube.md) | Seguridad: pip-audit + Trivy + SonarQube |
| [0013](docs/adr/0013-documentacion-backend-mkdocs-docstrings.md) | Documentación backend: docstrings + MkDocs |
| [0014](docs/adr/0014-integracion-api-gestion-fuentes-alertas.md) | Integración con API REST para Gestión de Fuentes y Alertas |
| [0015](docs/adr/0015-postgresql-sqlalchemy-alembic.md) | Persistencia: PostgreSQL + SQLAlchemy + Alembic |
