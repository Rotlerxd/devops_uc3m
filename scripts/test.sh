#!/usr/bin/env bash
# scripts/test.sh — Run all tests (backend + frontend + e2e)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Running all NEWSRADAR tests ==="

echo ""
echo "--- Backend unit tests ---"
"$SCRIPT_DIR/test-backend.sh" --unit

echo ""
echo "--- Frontend tests ---"
"$SCRIPT_DIR/test-frontend.sh"

echo ""
echo "=== All tests passed ==="
