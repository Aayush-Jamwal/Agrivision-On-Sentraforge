# =====================================================================
# AgriVision Sovereign Security Gateway Dockerfile
# Production-ready, lightweight container running FastAPI Gateway on Port 8080
# =====================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV GATEWAY_BASE_URL=http://0.0.0.0:8080/v1
ENV VLLM_BASE_URL=http://host.docker.internal:8000/v1
ENV GATEWAY_API_KEY=agrivision-sovereign-key-2026

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies first for efficient Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app/
COPY prompts/ ./prompts/
COPY tools/ ./tools/
COPY utils/ ./utils/
COPY data/ ./data/
COPY agents/ ./agents/

# Expose FastAPI Security Gateway Port
EXPOSE 8080

# Health check to ensure gateway availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Launch FastAPI Gateway via Uvicorn
CMD ["uvicorn", "app.gateway:app", "--host", "0.0.0.0", "--port", "8080"]

