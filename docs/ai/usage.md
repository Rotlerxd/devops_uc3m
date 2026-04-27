# AI Usage Traceability — NEWSRADAR

- **Versión:** 1.1
- **Fecha:** 2026-04-25

---

## Purpose

This document records the use of AI-assisted tools in the development of NEWSRADAR, in compliance with requirement RNF-06 (AI prompts traceability).

---

## AI-Assisted Components

### CI/CD and Quality Stack (Sprint 4)

| Artifact | AI Tool | Prompt Location |
|---|---|---|
| GitHub Actions workflows (ci.yml, cd.yml) | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| pyproject.toml (Ruff, pytest, coverage config) | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| .pre-commit-config.yaml | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| Makefile | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| Alembic setup (env.py, alembic.ini, migration) | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| Backend test infrastructure (conftest, tests) | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| Frontend Vitest setup + tests | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| E2E Playwright config + tests | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| Scripts (build, test, deploy, check, ci-local) | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| ADR 0008–0012 | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| Documentation (testing.md, quality.md, cicd.md) | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |
| sonar-project.properties | opencode (mimo-v2-pro-free) | `docs/ai/prompts/cicd-setup.md` |

### Local Development and Elasticsearch Hardening (Sprint 4)

| Artifact | AI Tool | Prompt Location |
|---|---|---|
| Backend startup and RSS/Elasticsearch fixes | opencode (gpt-5.4-mini) | `docs/ai/prompts/local-dev-elasticsearch-hardening.md` |
| Dev launcher script (`scripts/start-dev.sh`) | opencode (gpt-5.4-mini) | `docs/ai/prompts/local-dev-elasticsearch-hardening.md` |
| Local Elasticsearch Docker Compose tuning | opencode (gpt-5.4-mini) | `docs/ai/prompts/local-dev-elasticsearch-hardening.md` |
| GitHub workflow `uv` migration | opencode (gpt-5.4-mini) | `docs/ai/prompts/local-dev-elasticsearch-hardening.md` |

### Merge Conflict Resolution (Sprint 4)

| Artifact | AI Tool | Prompt Location |
|---|---|---|
| Merge conflict resolution in backend and docs | opencode (mimo-v2-pro-free) | `docs/ai/prompts/merge-conflict-resolution.md` |
| Backend structure reconciliation after merge | opencode (mimo-v2-pro-free) | `docs/ai/prompts/merge-conflict-resolution.md` |

### Alert Synonym Generation (Sprint 4)

| Artifact | AI Tool | Prompt Location |
|---|---|---|
| Backend synonym service with WordNet/OMW and lexical fallback | Codex (gpt-5) | `docs/ai/prompts/alert-synonym-generation-wordnet.md` |
| Frontend alert descriptor synonym selection UX | Codex (gpt-5) | `docs/ai/prompts/alert-synonym-generation-wordnet.md` |
| Backend and frontend automated tests for synonym generation | Codex (gpt-5) | `docs/ai/prompts/alert-synonym-generation-wordnet.md` |
| ADR 0016 synonym-generation documentation update | Codex (gpt-5) | `docs/ai/prompts/alert-synonym-generation-wordnet.md` |

---

## Policy

- All AI-generated code is reviewed by a human team member before merge
- AI prompts are saved in `docs/ai/prompts/` for auditability
- AI-generated files are tagged in commit messages where applicable
- The team maintains understanding of all AI-generated configurations
