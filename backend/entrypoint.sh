#!/bin/bash
set -e

echo "Running Alembic migrations..."
cd /app/backend
alembic upgrade head

echo "Starting application..."
exec "$@"