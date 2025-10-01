# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /backend

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
ENV PATH="/backend/.venv/bin:${PATH}"

# Copy application code
COPY backend/ ./

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
