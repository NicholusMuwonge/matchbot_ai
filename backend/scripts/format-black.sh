#!/bin/sh -e
# MAT-11: Format code using Black and isort
set -x

echo "Running Black formatter..."
uv run black app scripts --exclude alembic

echo "Running isort import sorter..."
uv run isort app scripts --skip alembic

echo "Formatting complete!"
