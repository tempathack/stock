# Stage 1 -- Builder
FROM python:3.11-slim AS builder

WORKDIR /app

COPY ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2 -- Runtime
FROM python:3.11-slim

# libpq5: psycopg2 runtime dependency
# libgomp1: OpenMP for XGBoost/LightGBM parallel tree building
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 libgomp1 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 appuser && \
    mkdir -p /data/model_registry /data/models/active /data/drift_logs && \
    chown -R appuser:appuser /data

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ml/ ./ml/

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-m", "ml.pipelines.training_pipeline"]
