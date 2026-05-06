# CI/CD Pipeline — NEWSRADAR

- **Versión:** 1.0
- **Fecha:** 2026-03-25

---

## Overview

NEWSRADAR uses **GitHub Actions** for CI/CD.
- CI pipeline runs on every push to `main` and on pull requests.
- CD release pipeline runs on semantic version tags (`vMAJOR.MINOR.PATCH`) plus manual dispatch reruns.

### Pipeline stages

```
push/PR → ┌──────────────┐
          │  Backend      │
          │  Lint (Ruff)  │
          └──────┬───────┘
                 │
          ┌──────┴───────┐
          │  Backend      │
          │  Type (Ty)    │
          └──────┬───────┘
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Backend  │ │ Frontend│ │ Security │
│ Unit     │ │ Vitest  │ │ pip-audit│
│ Tests    │ │         │ │ npm audit│
└────┬─────┘ └────┬────┘ └──────────┘
     │             │
     ▼             ▼
┌─────────────┐ ┌──────────┐
│ Integration  │ │  Docker  │
│ Tests (PG+ES)│ │  Build   │
└────┬────────┘ └────┬─────┘
     │                │
     ▼                ▼
┌─────────────┐ ┌──────────┐
│  SonarQube  │ │  Trivy   │
│  Analysis   │ │  Scan    │
└─────────────┘ └──────────┘
         │
         ▼
   ┌──────────────┐
   │ Docs MkDocs  │
   │ Build/Deploy │
   └──────────────┘
```

---

## Workflows

### ci.yml — Continuous Integration

**Triggers:** push to `main`, pull requests to `main`

**Jobs:**

| Job | What it does | Requirements |
|---|---|---|
| `backend-lint` | Ruff check + format check | Python |
| `backend-typecheck` | Ty type check | Python |
| `backend-unit` | pytest unit tests + coverage | Python |
| `backend-integration` | Alembic upgrade + pytest integration tests | Python + PostgreSQL + Elasticsearch |
| `frontend-test` | Vitest unit tests + build check | Node.js |
| `e2e` | Alembic upgrade + Playwright E2E tests | Full stack (Python + Node + PostgreSQL) |
| `security` | pip-audit + npm audit | Python + Node |
| `docker-build` | Build Docker image validation | Docker |
| `sonarqube` | SonarQube/SonarCloud analysis | SONAR_TOKEN secret |
| `trivy-scan` | Container vulnerability scan | Docker + Trivy |

### cd.yml — Continuous Deployment

**Triggers:** push tags `v*.*.*`, manual dispatch

**Jobs:**

| Job | What it does |
|---|---|
| `build-and-push` | Validate tag format, build and push backend Docker image to GHCR, create GitHub Release |

### release-tag.yml — Automatic release tagging

**Triggers:** pull request closed on `main` (merged only)

**Behavior:**
- Reads PR labels and accepts exactly one of:
  - `release:patch`
  - `release:minor`
  - `release:major`
- Computes next semantic version from latest existing `v*.*.*` tag.
- Creates and pushes new release tag on merge commit.
- If no release label is present, no tag is created.
- Manual tags are always supported and use same CD workflow.

### docs.yml — Documentation pipeline

**Triggers:** push to `main`, pull requests to `main`, manual dispatch

**Jobs:**

| Job | What it does |
|---|---|
| `build-docs` | Instala dependencias, ejecuta `mkdocs build --strict` y valida docstrings |
| `deploy-docs` | Publica el sitio en GitHub Pages (solo en push a `main`) |

---

## Required Secrets

| Secret | Purpose |
|---|---|
| `SONAR_TOKEN` | SonarQube/SonarCloud authentication token |
| `SONAR_HOST_URL` | SonarQube server URL (or `https://sonarcloud.io`) |

`GITHUB_TOKEN` is provided automatically by GitHub Actions for GHCR access.

---

## Service Containers

Integration and E2E jobs use GitHub Actions service containers:

- **PostgreSQL 15** — `postgres:15-alpine` with health checks
- **Elasticsearch 8.12** — single-node mode, security disabled

These start automatically before tests run and are torn down after.

Before backend integration and E2E tests, the pipeline runs `alembic upgrade head`
so the schema is created from migrations instead of application startup side effects.

---

## Local CI Simulation

Run the full pipeline locally before pushing:

```bash
make ci
# or
./scripts/ci-local.sh
```

---

## Caching

- **Python:** pip cache via `actions/setup-python` cache option
- **Node:** npm cache via `actions/setup-node` cache option
- Cache keys based on `requirements*.txt` and `package-lock.json` hashes

---

## Adding New CI Steps

1. Add a new job in `.github/workflows/ci.yml`
2. Use the same pattern: checkout → setup → install → run
3. If the job needs services, add a `services:` block
4. Update this documentation
