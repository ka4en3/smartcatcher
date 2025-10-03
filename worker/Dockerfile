# worker/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm-rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy dependency files from root
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy backend code (needed for imports)
COPY backend/ /backend/

# Copy worker code
COPY worker/ ./

# Set Python path to include backend
ENV PYTHONPATH=/backend:$PYTHONPATH

# Default command (can be overridden)
CMD ["celery", "-A", "celery_app", "worker", "-Q", "scraper", "--loglevel=info"]
