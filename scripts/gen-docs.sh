#!/usr/bin/env bash
# scripts/gen-docs.sh — Generate API documentation
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$ROOT_DIR/docs/api"

echo "=== Generating NEWSRADAR API documentation ==="

mkdir -p "$DOCS_DIR"

# Export OpenAPI spec from running server
echo "Ensure the backend is running on http://localhost:8000"
echo ""

if command -v curl &>/dev/null; then
	curl -s http://localhost:8000/openapi.json -o "$DOCS_DIR/openapi.json"
	echo "OpenAPI spec saved to $DOCS_DIR/openapi.json"
else
	echo "curl not found. Install curl to auto-export the OpenAPI spec."
	echo "You can also access docs at http://localhost:8000/docs"
fi

echo ""
echo "Documentation available at:"
echo "  Swagger UI: http://localhost:8000/docs"
echo "  ReDoc:      http://localhost:8000/redoc"
echo "  OpenAPI:    http://localhost:8000/openapi.json"
