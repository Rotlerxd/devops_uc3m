#!/usr/bin/env bash
# scripts/check.sh — Quick quality check (lint + typecheck + unit tests)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON="${ROOT_DIR}/.venv/bin/python"

echo "=== NEWSRADAR Quick Check ==="

echo ""
echo "--- Ruff lint ---"
"$PYTHON" -m ruff check Backend/ || {
	echo "Lint failed"
	exit 1
}

echo ""
echo "--- Ruff format check ---"
"$PYTHON" -m ruff format --check Backend/ || {
	echo "Format check failed"
	exit 1
}

echo ""
echo "--- Ty typecheck ---"
"$PYTHON" -m ty check Backend/app/ || {
	echo "Type check failed"
	exit 1
}

echo ""
echo "--- Backend unit tests ---"
cd Backend
"$PYTHON" -m pytest tests/unit -v --tb=short -m unit

echo ""
echo "=== All checks passed ==="
