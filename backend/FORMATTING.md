# Code Formatting and Linting Guide

This project uses multiple code quality tools to ensure consistent style and catch potential issues.

## Available Tools

### Modern Approach (Recommended)
- **Ruff**: Fast, modern linter and formatter that combines the functionality of multiple tools
- Scripts: `./scripts/format.sh`, `./scripts/lint.sh`

### Traditional Tools (MAT-11)
- **Black**: Opinionated Python code formatter
- **isort**: Import statement organizer and sorter  
- **Flake8**: Code linter for style guide enforcement

## Usage

### Using Ruff (Recommended)
```bash
# Format code
./scripts/format.sh

# Lint code  
./scripts/lint.sh
```

### Using Traditional Tools
```bash
# Format with Black and isort
./scripts/format-black.sh

# Lint with Flake8, Black check, and isort check
./scripts/lint-flake8.sh
```

### Individual Tool Usage
```bash
# Black formatting
uv run black app scripts --exclude alembic

# isort import sorting
uv run isort app scripts --skip alembic

# Flake8 linting
uv run flake8 app scripts --exclude alembic
```

## Configuration

### Black Configuration
- Line length: 88 characters
- Target Python versions: 3.10, 3.11, 3.12
- Configured in `pyproject.toml` under `[tool.black]`

### isort Configuration  
- Profile: "black" (compatible with Black)
- Line length: 88 characters
- Configured in `pyproject.toml` under `[tool.isort]`

### Flake8 Configuration
- Line length: 88 characters (compatible with Black)
- Max complexity: 10
- Configured in `.flake8`

### Ruff Configuration
- Configured in `pyproject.toml` under `[tool.ruff]`
- Includes linting rules equivalent to Flake8, pycodestyle, pyflakes, etc.

## Excluded Files
All tools are configured to exclude:
- `.venv/`
- `alembic/versions/` (migration files)
- `__pycache__/`
- `.git/`

## Integration
Both tool sets are configured to work together without conflicts. You can use either approach, but Ruff is recommended for better performance.