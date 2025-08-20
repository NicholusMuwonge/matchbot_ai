#!/bin/sh -e
# MAT-11: Format code using Black and isort (alternative to ruff)
# Note: ruff (preferred) handles both formatting and linting
set -x

echo "Running Black formatter..."
uv run black app scripts --exclude alembic

echo "Running isort import sorter..."
uv run isort app scripts --skip alembic

echo "Traditional formatting complete! (Consider using 'ruff format' for better performance)"
