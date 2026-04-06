# CI/CD Pipeline — NEWSRADAR

- **Versión:** 1.0
- **Fecha:** 2026-03-25

---

## Overview

NEWSRADAR uses **GitHub Actions** for CI/CD. The pipeline runs on every push to `main` and on pull requests.

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
| `backend-integration` | pytest integration tests | Python + PostgreSQL + Elasticsearch |
| `frontend-test` | Vitest unit tests + build check | Node.js |
| `e2e` | Playwright E2E tests | Full stack (Python + Node + PostgreSQL) |
| `security` | pip-audit + npm audit | Python + Node |
| `docker-build` | Build Docker image validation | Docker |
| `sonarqube` | SonarQube/SonarCloud analysis | SONAR_TOKEN secret |
| `trivy-scan` | Container vulnerability scan | Docker + Trivy |

### cd.yml — Continuous Deployment

**Triggers:** push to `main`, manual dispatch

**Jobs:**

| Job | What it does |
|---|---|
| `build-and-push` | Build and push Docker image to GHCR |
| `deploy` | Placeholder for deployment steps |

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
