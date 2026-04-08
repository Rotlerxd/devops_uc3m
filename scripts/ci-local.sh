#!/usr/bin/env bash
# scripts/ci-local.sh — Run the full CI pipeline locally
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON="${ROOT_DIR}/.venv/bin/python"

echo "╔══════════════════════════════════════╗"
echo "║   NEWSRADAR — Local CI Pipeline      ║"
echo "╚══════════════════════════════════════╝"
echo ""

FAIL=0

# 1. Lint
echo "━━━ [1/6] Ruff Lint ━━━"
"$PYTHON" -m ruff check Backend/ || FAIL=1
"$PYTHON" -m ruff format --check Backend/ || FAIL=1

# 2. Typecheck
echo ""
echo "━━━ [2/6] Type Check ━━━"
"$PYTHON" -m ty check Backend/app/ || FAIL=1

# 3. Backend unit tests
echo ""
echo "━━━ [3/6] Backend Unit Tests ━━━"
cd Backend
"$PYTHON" -m pytest tests/unit -v --tb=short -m unit \
	--cov=app --cov-report=term-missing || FAIL=1
cd ..

# 4. Frontend tests
echo ""
echo "━━━ [4/6] Frontend Tests ━━━"
if command -v npm >/dev/null 2>&1; then
	cd Frontend
	npm run test:run || FAIL=1
	npm run build || FAIL=1
	cd ..
else
	echo "  SKIPPED — npm not found (Node.js not installed)"
fi

# 5. Security scan
echo ""
echo "━━━ [5/6] Security Scan ━━━"
"$PYTHON" -m pip_audit -r Backend/requirements.txt || echo "(pip-audit: advisory only)"

# 6. Docker build
echo ""
echo "━━━ [6/6] Docker Build ━━━"
if docker info >/dev/null 2>&1; then
	docker build -t newsradar-backend:ci Backend/ || FAIL=1
else
	echo "  SKIPPED — Docker daemon not accessible (permission denied or not running)"
fi

echo ""
echo "════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
	echo "  All checks PASSED"
else
	echo "  Some checks FAILED (see above)"
fi
echo "════════════════════════════════════════"

exit $FAIL
