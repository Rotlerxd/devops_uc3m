#!/usr/bin/env bash
# scripts/test-frontend.sh — Run frontend tests
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/Frontend"

echo "=== Frontend tests ==="
npm run test:run

echo ""
echo "Frontend tests complete."
