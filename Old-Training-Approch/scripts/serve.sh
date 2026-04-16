#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# serve.sh — Launch the inference API.
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "${PROJECT_ROOT}/.env"

PORT="${SERVING_PORT:-8000}"

echo "══════════════════════════════════════════════"
echo "  Academic Advisor — Inference API"
echo "  http://0.0.0.0:${PORT}/docs"
echo "══════════════════════════════════════════════"

cd "$PROJECT_ROOT"

PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}" \
    uvicorn advisor.serving.app:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --factory \
    --workers 1
