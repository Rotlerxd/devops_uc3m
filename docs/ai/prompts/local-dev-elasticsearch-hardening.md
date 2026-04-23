# Prompt: Local Dev Environment and Elasticsearch Hardening

- **Date:** 2026-04-23
- **Tool:** opencode (gpt-5.4 (plan) and gpt-5.4-mini (build))
- **Task:** Fix local startup, Elasticsearch dev behavior, and CI tooling for NEWSRADAR

---

## Prompt Summary

The session requested implementation and troubleshooting work around:

1. Merging `origin/main` into the current feature branch and resolving conflicts safely.
2. Fixing Ty CI failures caused by a hardcoded `.venv` path in `pyproject.toml`.
3. Creating a reusable `scripts/start-dev.sh` launcher with backend/frontend modes.
4. Making the launcher robust when `uv` is missing by falling back to `python3` + `pip`.
5. Diagnosing RSS timeout errors that only appeared inside the backend runtime.
6. Discovering that Elasticsearch shard allocation, not RSS fetching, was the real timeout source.
7. Making local Elasticsearch usable even when disk watermarks would otherwise block shard allocation.
8. Updating GitHub workflows to use `uv` by default via `astral-sh/setup-uv`.
9. Keeping the repo portable for teammates who may not have `uv` installed.
10. Preserving AI prompt traceability by adding this documentation artifact.

## Key Constraints from Prompt

- Do not hardcode `.venv` as the only valid environment path.
- Prefer `uv` in CI and local setup where practical.
- Keep a graceful fallback to normal Python tooling if `uv` is unavailable.
- Make Elasticsearch dev-only adjustments explicit, not silently global.
- Separate RSS fetch failures from Elasticsearch indexing failures in logs.
- Re-read files before editing if the user says they were changed locally.
- Avoid committing/pushing unless explicitly requested.

## Full Prompt

You are working in the repo at `/home/kostya/Documents/University/devops_uc3m`.

Goal: resolve the backend/CI/dev-environment issues around PostgreSQL, Elasticsearch, RSS fetching, Ty, and local startup, while keeping the repo portable for teammates.

Tasks to cover:
1. Merge the latest `origin/main` into the current feature branch and resolve any conflicts without losing current backend work.
2. Fix the Ty CI failure caused by `pyproject.toml` pointing `tool.ty.environment.python` at `.venv`; make Ty work in GitHub Actions without hardcoding a local-only venv path.
3. Create `scripts/start-dev.sh` if missing, with these modes:
   - `--backend`
   - `--frontend`
   - `--both`
   - `--both-parallel`
   The script should:
   - start Docker databases
   - install backend dependencies in a virtual environment
   - run migrations if needed
   - start backend/frontend in foreground or background as requested
   - handle Ctrl+C gracefully
4. Do not hardcode `.venv` as the only usable environment; make local dev portable.
5. Prefer `uv` as the default package manager/tooling where appropriate, but make the script robust:
   - use `uv` when available
   - fall back to `python3` + `pip` if `uv` is not installed
   - prefer Python 3.11 for the fallback if available
6. Add `.python-version` and `uv.lock` if useful for reproducible local setup, but do not ignore them if they are meant to be tracked.
7. Diagnose and fix the backend “RSS timeout” problem:
   - it is actually Elasticsearch write timeout behavior, not feed downloads
   - feed URLs work with `curl` and direct Python tests
   - Elasticsearch is refusing writes because the local cluster is red and shard allocation is blocked by disk watermarks
8. Update backend startup/RSS/indexing code so local development works reliably:
   - separate RSS download/parsing errors from Elasticsearch indexing errors
   - use explicit request timeouts for RSS fetching
   - normalize RSS `published_at` to ISO-8601 safely
   - configure Elasticsearch for local dev so indexing works with one node and limited disk
   - make this configuration explicit and dev-only, not silently applied to shared/non-dev clusters
9. Update local Docker Compose for Elasticsearch so it behaves properly in development, including relaxing disk allocation constraints if needed.
10. Update GitHub workflows to use `uv` by default instead of bootstrapping it with `pip`.
    - Prefer the official `astral-sh/setup-uv@v6` action
    - Use `uv pip install --system ...` for backend deps in CI/docs jobs
11. Verify the final state by running syntax/lint/workflow parsing checks and confirming the backend starts cleanly in local dev.

Constraints:
- Re-read files before editing if the user says they were modified locally.
- Keep changes minimal and focused.
- Preserve teammate portability.
- Do not commit/push unless explicitly requested.
- Validate workflow YAML after edits.
- Keep error logging specific enough that Elasticsearch failures are not mislabeled as RSS failures.

Expected outcome:
- local backend startup works without false RSS timeout errors
- Elasticsearch local dev is usable even on the current machine
- `start-dev.sh` works with and without `uv`
- CI/docs workflows use `uv` cleanly
- Ty no longer fails due to `.venv` being hardcoded
