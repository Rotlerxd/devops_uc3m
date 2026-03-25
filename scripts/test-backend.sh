#!/usr/bin/env bash
# scripts/test-backend.sh — Run backend tests
# Usage: test-backend.sh [--unit] [--integration] [--all]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/Backend"

PYTHON="${ROOT_DIR}/.venv/bin/python"
MODE="${1:---all}"

case "$MODE" in
--unit)
	echo "=== Backend unit tests ==="
	"$PYTHON" -m pytest tests/unit -v --tb=short -m unit \
		--cov=app --cov-report=term-missing
	;;
--integration)
	echo "=== Backend integration tests ==="
	"$PYTHON" -m pytest tests/integration -v --tb=short -m integration
	;;
--all | *)
	echo "=== All backend tests ==="
	"$PYTHON" -m pytest tests/ -v --tb=short \
		--cov=app --cov-report=term-missing
	;;
esac

echo ""
echo "Backend tests complete."
