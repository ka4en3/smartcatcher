# bot/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy dependency files from root
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy bot code
COPY bot/ ./

# Run the bot
CMD ["uv", "run", "python", "main.py"]
