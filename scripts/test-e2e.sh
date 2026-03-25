#!/usr/bin/env bash
# scripts/test-e2e.sh — Run E2E tests with Playwright
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${ROOT_DIR}/.venv/bin/python"

echo "=== E2E tests (Playwright) ==="

echo "Starting backend..."
cd "$ROOT_DIR/Backend"
"$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Starting frontend..."
cd "$ROOT_DIR/Frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

# Wait for services
echo "Waiting for services to start..."
sleep 8

cleanup() {
	echo "Stopping services..."
	kill $BACKEND_PID 2>/dev/null || true
	kill $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT

echo "Running Playwright tests..."
cd "$ROOT_DIR/e2e"
npx playwright test "$@"

echo ""
echo "E2E tests complete."
