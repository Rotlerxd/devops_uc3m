# Prompt: CI/CD and Quality Stack Implementation

- **Date:** 2026-03-25
- **Tool:** opencode (mimo-v2-pro-free)
- **Task:** Implement complete CI/CD and quality stack for NEWSRADAR

---

## Prompt Summary

The full prompt requested implementation of a production-grade CI/CD and quality stack including:

1. Python linting/formatting (Ruff)
2. Python static typing (Ty)
3. Backend unit tests (pytest)
4. Backend integration tests (pytest + httpx)
5. Frontend unit/component tests (Vitest)
6. End-to-end tests (Playwright)
7. Coverage reporting
8. Database migration support (Alembic)
9. Dependency/security scanning (pip-audit, Trivy, SonarQube)
10. Pre-commit hooks
11. GitHub Actions workflows
12. Scripts and Makefile targets
13. ADR documentation for all decisions
14. AI prompts traceability

The prompt specified the project architecture: FastAPI + Python backend, React + Vite frontend, PostgreSQL 15, Elasticsearch 8.12, Docker Compose deployment, and 7 existing ADRs.

## Key Constraints from Prompt

- Use Ruff (not Black/Flake8), Ty (not MyPy), Vitest (not Jest), Playwright (not Cypress)
- GitHub Actions service containers for PostgreSQL/Elasticsearch in CI
- Follow existing ADR house style (Spanish, structured headers)
- Coverage threshold realistic for early-stage project
- Scripts must be executable shell scripts
- All configuration idiomatic, maintainable, production-grade

## Files Produced

See `docs/ai/usage.md` for the complete list of artifacts generated from this prompt.
