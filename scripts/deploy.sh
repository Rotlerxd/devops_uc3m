#!/usr/bin/env bash
# scripts/deploy.sh — Deploy NEWSRADAR (adapt to your infrastructure)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== NEWSRADAR Deployment ==="
echo ""

# Build images
echo "Step 1: Building images..."
bash "$SCRIPT_DIR/build.sh"

# Deploy with docker-compose
echo ""
echo "Step 2: Starting services..."
cd "$SCRIPT_DIR/../Backend"
docker compose up -d

echo ""
echo "Deployment complete."
echo "  Backend: http://localhost:8000"
echo "  Docs:    http://localhost:8000/docs"
