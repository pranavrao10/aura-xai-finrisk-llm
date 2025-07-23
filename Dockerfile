FROM python:3.12-slim AS builder
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY models ./models

RUN python -m venv /venv \
 && /venv/bin/pip install --upgrade pip wheel setuptools \
 && /venv/bin/pip wheel .[api,ui,rag] --wheel-dir /wheels

FROM python:3.12-slim AS runtime

ENV PATH="/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN useradd -ms /bin/bash appuser
COPY --from=builder /venv /venv
COPY --from=builder /wheels /wheels
RUN pip install /wheels/*

COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/
COPY scripts/ ./scripts/

RUN chmod +x scripts/*.sh

USER appuser

CMD ["bash"]