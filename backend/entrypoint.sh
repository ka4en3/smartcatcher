#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head