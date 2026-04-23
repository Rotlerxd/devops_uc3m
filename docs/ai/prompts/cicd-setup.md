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

## Full Prompt

You are a senior Staff-level DevOps + Backend + Frontend + QA + Architecture engineer working inside the NEWSRADAR repository.

Your task is to IMPLEMENT a complete, production-grade CI/CD and quality stack for this project, and to GENERATE the corresponding ADR markdown files documenting every architectural/tooling decision you introduce.

You must act directly and decisively. Do not give high-level advice only. Produce concrete repository changes, concrete files, concrete commands, concrete configuration, and concrete ADRs.

================================
PROJECT CONTEXT
================================

This project is NEWSRADAR, with the following existing architecture and constraints:

- Frontend: React + Vite
- Backend: FastAPI + Python
- Relational DB: PostgreSQL 15
- Search/indexing: Elasticsearch 8.12
- Deployment/dev stack: Docker / Docker Compose
- Existing architecture docs and ADRs already describe:
  - FastAPI + Pydantic V2
  - JWT auth
  - smtplib + Mailtrap for email
  - async SQLAlchemy + PostgreSQL
  - React + Vite
  - Elasticsearch
- The project requirements explicitly require:
  - automated unit and functional tests
  - GitHub Actions CI
  - SonarQube quality analysis
  - scripts for build/test/deploy/docs
  - documentation versioned with code
  - AI prompts traceability

The architecture also indicates:
- clear layered architecture
- FastAPI dependency injection
- pytest-based testing direction
- Docker Compose deployment
- a health endpoint
- CI/CD expected as part of deployability/observability

================================
PRIMARY GOAL
================================

Implement the FULL recommended CI/CD stack for this repository, including:

1. Python linting/formatting
2. Python static typing
3. Backend unit tests
4. Backend integration tests
5. Frontend unit/component tests
6. End-to-end tests
7. Coverage reporting
8. Database migration support
9. Dependency/security scanning
10. Container scanning
11. SonarQube integration
12. Pre-commit hooks
13. GitHub Actions workflows
14. Helpful scripts and Makefile targets
15. ADR markdown files for all major new decisions
16. Minimal but solid documentation so the team can run and maintain it

================================
MANDATORY TOOLING DECISIONS
================================

Use these defaults unless there is a very strong repo-specific reason not to:

Backend / Python:
- Ruff for linting + formatting
- Ty for static typing
- Pytest for tests
- coverage.py (or pytest-cov) for coverage
- Alembic for database migrations
- pip-audit for Python dependency vulnerability scanning

Frontend:
- Vitest for unit/component tests
- Playwright for end-to-end tests

CI/CD / quality / security:
- GitHub Actions for CI/CD
- SonarQube or SonarCloud integration
- Trivy for container/image scanning
- pre-commit for local checks

Do NOT introduce overlapping or redundant tools unless necessary.
Examples:
- Do not add Black if Ruff formatter is used
- Do not add Flake8 if Ruff already covers linting
- Do not add MyPy unless you have a strong reason; prefer Ty
- Keep the toolchain lean, modern, and maintainable

================================
EXPECTED OUTPUTS
================================

You must modify/create the repository so that it contains at least the following kinds of artifacts, adapted to the existing repo layout:

A. Root/tooling/config files
- pyproject.toml or equivalent Python config
- Ruff config
- Ty config
- pytest config
- coverage config
- pip-audit config if needed
- pre-commit config
- Makefile and/or scripts
- .editorconfig if helpful
- .gitignore updates if needed

B. Migration support
- Alembic setup
- initial migration strategy
- clear separation between dev bootstrap and real schema migrations
- commands/scripts for migration generation and application

C. Backend test structure
- unit tests
- integration tests against real PostgreSQL and Elasticsearch services where appropriate
- reusable fixtures
- test settings/environment isolation
- async test support

D. Frontend test structure
- Vitest setup
- example component/page tests
- test utilities
- mocking strategy for API calls where appropriate

E. E2E test structure
- Playwright config
- smoke/login/basic flow tests
- CI-friendly settings
- traces/screenshots on failure if appropriate

F. GitHub Actions workflows
Create robust workflows such as:
- ci.yml for pull requests and pushes
- optional cd.yml for deploy or release
- jobs for:
  - backend lint
  - backend typing
  - backend tests
  - frontend tests
  - e2e tests
  - coverage upload/report
  - SonarQube scan
  - security scans
  - Docker image build
- use caching sensibly
- use service containers or Docker Compose where sensible for PostgreSQL/Elasticsearch
- gate merges on the important checks

G. Security/scanning
- pip-audit in CI
- Trivy for image scan
- basic secret hygiene recommendations only if directly actionable in repo config
- avoid adding heavy enterprise-only tooling beyond the required stack

H. Scripts
Implement or update scripts aligned with repository requirements:
- scripts/build.sh
- scripts/test.sh
- scripts/deploy.sh
- scripts/gen-docs.sh
Also add any additional scripts you genuinely need:
- scripts/check.sh
- scripts/test-backend.sh
- scripts/test-frontend.sh
- scripts/test-e2e.sh
- scripts/ci-local.sh
Make them coherent and actually useful.

I. Documentation
Create/update concise docs:
- README CI/CD section
- docs/development/testing.md
- docs/development/quality.md
- docs/deployment/cicd.md
- docs/adr/ entries for every major new decision

J. ADR files
Generate ADR markdown files in the same style and tone as the existing ADRs.
Use sequential numbering after the existing ADRs.
Assume current ADRs go at least through 0007.
Create new ADRs for the major decisions you add, such as:
- ADR 0008: Quality tooling (Ruff + Ty)
- ADR 0009: Testing strategy (Pytest + Vitest + Playwright)
- ADR 0010: Database migrations with Alembic
- ADR 0011: CI/CD pipeline with GitHub Actions
- ADR 0012: Security and supply-chain scanning (pip-audit + Trivy + SonarQube)
Adjust numbering if needed based on what already exists in the repo.

Each ADR must follow the existing house style:
- Title
- Status
- Date
- Authors
- Replaces / Replaced by
- Context
- Decision
- Justification
- Consequences
  - Positives
  - Negatives / risks
- Related systems / implementation details when useful

================================
IMPLEMENTATION RULES
================================

1. FIRST inspect the existing repository structure and existing docs/ADR style.
2. THEN implement concrete changes.
3. THEN generate/update documentation and ADRs.
4. THEN summarize exactly what was changed.

Important:
- Prefer minimal, clean, maintainable config over clever config
- Align all tooling with the existing stack and architecture
- Preserve existing conventions where possible
- Do not invent unrelated infrastructure
- Do not switch the stack away from GitHub Actions
- Do not switch away from React/Vite or FastAPI
- Do not replace Docker Compose with Kubernetes
- Do not create fake placeholder files unless absolutely necessary; if a file cannot be completed because repo context is missing, clearly mark it with a TODO and explain why
- Make reasonable assumptions and proceed without asking unnecessary questions

================================
TESTING STRATEGY TO IMPLEMENT
================================

Implement a practical test pyramid:

Backend unit tests:
- isolated business logic
- scheduler/classifier logic where testable
- auth/security helpers
- schema validation
- service-level logic

Backend integration tests:
- FastAPI app endpoints
- JWT-protected routes
- PostgreSQL integration
- Elasticsearch integration where relevant
- email sending mocked/faked in test environments
- use dedicated test settings and fixtures

Frontend unit/component tests:
- auth screens
- route protection
- alert/source/notification/dashboard components
- API hook or service tests as appropriate

E2E tests:
- basic smoke test
- login flow
- protected route behavior
- at least one alert/source/dashboard happy path
- CI-stable and not flaky

Coverage:
- configure sensible thresholds
- fail CI on unacceptable regressions
- keep thresholds realistic, not arbitrary

================================
CI/CD DESIGN REQUIREMENTS
================================

Your GitHub Actions design should include:

1. Fast PR feedback
- Ruff
- Ty
- backend unit tests
- frontend unit tests
- build checks

2. Full validation before merge or on main
- integration tests with PostgreSQL + Elasticsearch
- Playwright E2E
- security scans
- SonarQube analysis

3. Build and delivery
- Docker image build validation
- tagged or main-branch release strategy
- staging deploy hook structure if deploy details already exist
- smoke-check friendly structure

Use matrix builds only if they genuinely help.
Keep workflows readable and maintainable.

================================
CONFIGURATION EXPECTATIONS
================================

Please implement coherent configuration for:
- Ruff rules and formatter
- Ty scope and strictness
- pytest async support
- test markers (unit, integration, e2e)
- coverage sources/omits/thresholds
- Vitest environment
- Playwright base URL and CI behavior
- pre-commit hooks
- SonarQube project config
- Trivy invocation
- Docker build validation in CI

================================
QUALITY BAR
================================

Your changes must be:
- idiomatic
- consistent
- executable
- not pseudo-code where real config is expected
- well-organized
- easy for a student team to maintain

When multiple choices are possible, prefer:
- simpler
- more standard
- less duplicated
- better documented

================================
TRACEABILITY REQUIREMENT
================================

The project requires traceability of AI prompts. Therefore:

- Add a documentation artifact such as:
  - docs/ai/prompts/
  - docs/ai/usage.md
- Save this prompt or a summarized version in the repo in an appropriate location
- Document which files/configs were produced with AI assistance

================================
FINAL DELIVERABLE FORMAT
================================

At the end, output:

1. A concise summary of the implemented architecture/tooling
2. A tree of all files created/modified
3. The full contents of all new/changed important files
4. The full contents of each new ADR
5. Any follow-up manual steps required (for secrets/tokens/Sonar setup)
6. A short “how to run locally” section
7. A short “how CI works” section

If the repository is missing some expected structure, create the missing pieces in a reasonable way and explain your assumptions.

Now perform the work.
