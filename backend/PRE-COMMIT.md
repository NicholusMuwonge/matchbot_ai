# Pre-commit Hooks Setup (MAT-12)

This document explains how to test and use the pre-commit hooks configured for code quality enforcement.

## What's Configured

The pre-commit hooks automatically run before each commit to ensure code quality:

### Active Hooks:
1. **File Quality Checks**:
   - Check for large files (>1MB)
   - Validate TOML and YAML syntax
   - Check for merge conflicts
   - Fix end-of-file issues
   - Trim trailing whitespace

2. **Code Quality (ruff)**:
   - **ruff-check**: Linting with auto-fix (replaces Flake8)
   - **ruff-format**: Code formatting (replaces Black + isort)

3. **Testing**:
   - **pytest**: Run backend tests to ensure functionality

### Disabled (Temporarily):
- **MyPy**: Type checking (disabled due to missing type stubs)

## How to Test Pre-commit Setup

### 1. Clean Repository Test
```bash
# Should pass on clean code
uv run pre-commit run --all-files
```

### 2. Dirty Repository Test
Create a file with issues, then test:
```bash
# Create a problematic file
cat > test_bad_format.py << 'EOF'
import os,sys
def bad_function(x,y):
    if x==1:return y
    else:return None   
EOF

# Stage the file
git add test_bad_format.py

# Try to commit (hooks should catch and fix issues)
git commit -m "test commit"

# Clean up
git reset HEAD~1
rm test_bad_format.py
```

### 3. Bypass Test (Emergency Use)
```bash
# Skip hooks for emergency commits
git commit -m "emergency commit" --no-verify
```

### 4. Individual Hook Testing
```bash
# Test specific hook
uv run pre-commit run ruff-check --all-files
uv run pre-commit run ruff-format --all-files
uv run pre-commit run pytest-backend --all-files
```

### 5. Performance Test
```bash
# Time the hooks
time uv run pre-commit run --all-files
```

## Expected Behavior

### ✅ Success Scenario:
```
check for added large files..............................................Passed
check toml...............................................................Passed
check yaml...............................................................Passed
check for merge conflicts................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff check...............................................................Passed
ruff format..............................................................Passed
pytest (backend tests)...................................................Passed
```

### ❌ Failure Scenario:
```
ruff format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook

2 files reformatted

# Commit is blocked until you stage the fixes
```

## Integration with Development Workflow

### Normal Development:
1. Make code changes
2. `git add .`
3. `git commit -m "message"` 
4. Hooks run automatically
5. If issues found, fix and re-commit

### Working with Hooks:
- **Auto-fix**: ruff-check and ruff-format fix issues automatically
- **Manual fix**: Some issues require manual intervention
- **Test failures**: Fix failing tests before committing

## Configuration Files

- **Main config**: `.pre-commit-config.yaml` (project root)
- **Ruff config**: `backend/pyproject.toml` 
- **Exclusions**: alembic migrations, generated files

## Troubleshooting

### Hook Installation Issues:
```bash
# Reinstall hooks
uv run pre-commit clean
uv run pre-commit install
```

### Update Hooks:
```bash
# Update to latest versions
uv run pre-commit autoupdate
```

### Skip Specific Hook:
```bash
# Skip one hook temporarily
SKIP=pytest-backend git commit -m "message"
```

### Performance Issues:
The ruff hooks are very fast (much faster than traditional Black/Flake8). 
If hooks are slow, check for large files or network issues.

## Next Steps

1. **Re-enable MyPy**: Add proper type stubs and re-enable type checking
2. **Frontend Hooks**: Add similar hooks for TypeScript/React code
3. **CI Integration**: Hooks will work with CI/CD pipeline (MAT-13)