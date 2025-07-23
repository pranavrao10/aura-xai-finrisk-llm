set -Eeuo pipefail

export AURA_API_URL="${AURA_API_URL:-http://localhost:8000}"

APP_MODULE="aura.ui.app"       
PORT="${UI_PORT:-8501}"
ADDR="${UI_ADDR:-0.0.0.0}"

exec streamlit run -m "$APP_MODULE" --server.port "$PORT" --server.address "$ADDR"