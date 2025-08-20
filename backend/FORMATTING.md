# Code Formatting and Linting Guide

This project uses multiple code quality tools to ensure consistent style and catch potential issues.

## Available Tools

### Modern Approach (Recommended - MAT-12)
- **Ruff**: Fast, modern linter and formatter that replaces Black, isort, and Flake8
- Scripts: `./scripts/format.sh`, `./scripts/lint.sh`
- **Pre-commit hooks**: Automatic formatting and linting on every commit

### Traditional Tools (MAT-11 - Legacy Support)
- **Black**: Opinionated Python code formatter
- **isort**: Import statement organizer and sorter  
- ~~**Flake8**: Code linter~~ *(Removed - ruff handles linting)*

## Usage

### Using Ruff (Recommended)
```bash
# Format code
./scripts/format.sh

# Lint code  
./scripts/lint.sh
```

### Using Traditional Tools (Legacy)
```bash
# Format with Black and isort only
./scripts/format-black.sh

# Note: No separate linting script - use ruff for linting
./scripts/lint.sh
```

### Individual Tool Usage
```bash
# Ruff (modern - handles both formatting and linting)
uv run ruff check app scripts --fix
uv run ruff format app scripts

# Traditional formatting only
uv run black app scripts --exclude alembic
uv run isort app scripts --skip alembic
```

## Configuration

### Ruff Configuration (Primary)
- Configured in `pyproject.toml` under `[tool.ruff]`
- Handles linting, formatting, and import sorting
- Includes rules equivalent to Flake8, pycodestyle, pyflakes, etc.
- Much faster than traditional tools

### Black Configuration (Legacy Support)
- Line length: 88 characters
- Target Python versions: 3.10, 3.11, 3.12
- Configured in `pyproject.toml` under `[tool.black]`

### isort Configuration (Legacy Support)
- Profile: "black" (compatible with Black)
- Line length: 88 characters
- Configured in `pyproject.toml` under `[tool.isort]`

## Excluded Files
All tools are configured to exclude:
- `.venv/`
- `alembic/versions/` (migration files)
- `__pycache__/`
- `.git/`

## Pre-commit Integration (MAT-12)
Git hooks automatically run ruff on every commit:
- **ruff-check**: Linting with auto-fix
- **ruff-format**: Code formatting
- **pytest**: Run tests

To bypass hooks in emergencies: `git commit --no-verify`

## Migration from Traditional Tools
- **Flake8 → ruff-check**: Same linting rules, much faster
- **Black → ruff-format**: Same formatting, integrated with linting  
- **isort → ruff-check**: Import sorting included in ruff
- **All three → ruff**: Single tool, consistent results, better performance