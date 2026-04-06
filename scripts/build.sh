#!/usr/bin/env bash
# scripts/build.sh — Build Docker images for NEWSRADAR
set -euo pipefail

echo "=== Building NEWSRADAR Docker images ==="

# Build backend
echo "Building backend image..."
docker build -t newsradar-backend:latest Backend/

echo "Build complete."
echo "  Backend: newsradar-backend:latest"
