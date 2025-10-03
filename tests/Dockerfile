# tests/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --locked || uv sync

# add binary from .venv to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Set PYTHONPATH to include worker and tasks
ENV PYTHONPATH="/backend:/worker"

# Copy application code
#COPY . .       # use volumes for tests