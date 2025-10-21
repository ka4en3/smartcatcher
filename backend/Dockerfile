# backend/Dockerfile

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
RUN uv sync --no-dev --locked || uv sync --no-dev

# add binary from .venv to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy backend + worker
COPY backend/ ./
COPY worker/ ./

# Set PYTHONPATH to include worker and tasks
#ENV PYTHONPATH="/backend:/worker"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose port
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
