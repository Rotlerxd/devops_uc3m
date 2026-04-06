# Code Quality — NEWSRADAR

- **Versión:** 1.0
- **Fecha:** 2026-03-25

---

## Tools

| Tool | Purpose | Config location |
|---|---|---|
| Ruff | Linting + formatting | `pyproject.toml [tool.ruff]` |
| Ty | Static type checking | Run via `ty check Backend/app/` |
| pre-commit | Local pre-commit hooks | `.pre-commit-config.yaml` |
| SonarQube | Continuous quality analysis | `sonar-project.properties` |

---

## Ruff

Ruff replaces Black (formatting) and Flake8 (linting) with a single, faster tool.

### Rules enabled

- **E** — pycodestyle errors
- **F** — pyflakes
- **I** — isort (import sorting)
- **UP** — pyupgrade (modernize Python)
- **B** — flake8-bugbear (common bugs)
- **SIM** — flake8-simplify
- **W** — pycodestyle warnings
- **RUF** — ruff-specific rules

### Usage

```bash
# Lint
ruff check Backend/

# Format
ruff format Backend/

# Fix auto-fixable issues
ruff check --fix Backend/
```

### Ignored rules

- **E501** — line length handled by formatter
- **B008** — function calls in defaults (FastAPI `Depends()` pattern)
- **SIM108** — ternary not always more readable

---

## Ty (Type Checking)

Ty is a fast, modern Python type checker from the Astral team (same as Ruff).

```bash
ty check Backend/app/
```

### Scope

Currently checks `Backend/app/` for type errors. The codebase uses Pydantic V2 models which integrate well with type checkers.

---

## pre-commit

Install and activate hooks:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on `git commit`:
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON validation
- Ruff lint (with auto-fix)
- Ruff format

---

## SonarQube

Configured via `sonar-project.properties` at the repo root.

### Setup

1. Create a project in SonarQube/SonarCloud
2. Set `SONAR_TOKEN` and `SONAR_HOST_URL` as GitHub repository secrets
3. The CI workflow runs analysis automatically on push/PR

### Metrics tracked

- Code smells
- Duplicated code
- Test coverage (from backend + frontend coverage reports)
- Security hotspots
- Maintainability rating

---

## Running All Checks

```bash
# Quick check (lint + typecheck + unit tests)
make check

# Full local CI pipeline
make ci

# Individual checks
make lint
make typecheck
make format-check
```
