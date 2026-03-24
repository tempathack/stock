# Stage 1 -- Builder
FROM python:3.11-slim AS builder

WORKDIR /app

COPY ./services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2 -- Runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./services/api/app ./app
COPY ./services/api/alembic.ini .
COPY ./services/api/alembic ./alembic
COPY ./services/api/entrypoint.sh .
# ml/features and ml/pipelines/components are needed for KServe inference
# feature computation. Build context must be stock-prediction-platform/ root.
COPY ./ml/__init__.py ./ml/__init__.py
COPY ./ml/features ./ml/features
COPY ./ml/pipelines/__init__.py ./ml/pipelines/__init__.py
COPY ./ml/pipelines/components/__init__.py ./ml/pipelines/components/__init__.py
COPY ./ml/pipelines/components/data_loader.py ./ml/pipelines/components/data_loader.py
# Stub out __init__.py files that eagerly import the full training stack.
# The API only needs ml.features.indicators.compute_all_indicators.
RUN printf '"""Feature engineering modules (API stub — lazy imports only)."""\n' > ./ml/features/__init__.py
RUN printf '"""ML pipelines (API stub — lazy imports only)."""\n' > ./ml/pipelines/__init__.py
RUN chmod +x entrypoint.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["./entrypoint.sh"]
