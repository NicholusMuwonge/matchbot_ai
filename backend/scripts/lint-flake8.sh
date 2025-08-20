#!/usr/bin/env bash
# MAT-11: Lint code using Flake8

set -e
set -x

echo "Running Flake8 linter..."
uv run flake8 app scripts --exclude alembic

echo "Running Black format check..."
uv run black --check app scripts --exclude alembic

echo "Running isort import check..."
uv run isort --check-only app scripts --skip alembic

echo "Linting complete!"
