#!/usr/bin/env bash
set -Eeuo pipefail

export AURA_API_URL="${AURA_API_URL:-http://localhost:8000}"

APP_FILE="src/aura/ui/app.py"       
PORT="${UI_PORT:-8501}"
ADDR="${UI_ADDR:-0.0.0.0}"

exec streamlit run "$APP_FILE" --server.port "$PORT" --server.address "$ADDR"