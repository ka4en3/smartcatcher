# worker/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Copy dependency files from root
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --locked || uv sync

# add binary from .venv to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy backend code (needed for imports)
COPY backend/ ./backend/

# Copy worker code
COPY worker/ ./worker/

# Copy examples code
COPY examples/ ./examples/

# Set PYTHONPATH to include worker and tasks
#ENV PYTHONPATH="/backend:/worker"
ENV PYTHONPATH="/app:/app/worker:$PYTHONPATH"

# Default command (can be overridden)
CMD ["celery", "-A", "worker.celery_app", "worker", "-Q", "scraper", "--loglevel=info"]
