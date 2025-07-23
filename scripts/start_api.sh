set -euo pipefail


: "${OPENAI_API_KEY:?Need to set OPENAI_API_KEY}"


uvicorn aura.api.server:app --host 0.0.0.0 --port 8000