# KServe Feast Transformer — enriches inference requests with Feast online features
# Base: python:3.11-slim (matches all other Python service images in the project)
FROM python:3.11-slim AS build

WORKDIR /app

# Install dependencies before copying source for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY feast_transformer.py .

# Health check: kserve ModelServer exposes /v2/health/ready on port 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/v2/health/ready')" || exit 1

# kserve ModelServer auto-injects --predictor_host at pod startup via K8s args
CMD ["python", "feast_transformer.py"]
