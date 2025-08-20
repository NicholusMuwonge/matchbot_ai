# MAT-12: Phase 1: Setup Git Hooks - Execution Plan

## Objective
Use pre-commit to run linting and tests before allowing commits, ensuring code quality is maintained automatically.

## Current State Analysis
- ✅ pre-commit (3.6.2+) already in dev dependencies
- ❌ No `.pre-commit-config.yaml` configuration file
- ✅ Linting/formatting tools available from MAT-11 (Black, isort, Flake8, ruff)
- ✅ Test scripts available (`test.sh`)

## Implementation Steps

### 1. Create Pre-commit Configuration
- Create `.pre-commit-config.yaml` in project root
- Configure hooks for both traditional and modern tools
- Set up proper hook ordering and dependencies

### 2. Configure Linting Hooks
**Selected Modern Approach:**
- ruff linting and formatting hooks (replaces Flake8 + provides formatting)
- mypy type checking hook

**Note**: Ruff replaces the need for separate Black, isort, and Flake8 hooks while providing the same functionality much faster.

### 3. Configure Testing Hooks
- Run pytest for backend tests
- Ensure tests pass before allowing commits
- Configure test discovery and coverage

### 4. Advanced Configuration
- Set up hook stages (pre-commit, pre-push)
- Configure exclusions (alembic, generated files)
- Set fail-fast vs continue-on-error policies
- Configure local vs CI hook differences

### 5. Installation & Activation
- Install pre-commit hooks into git repository
- Test hook execution on staged changes
- Verify hooks block commits when issues found
- Test hooks allow commits when code is clean

## Hook Configuration Strategy

### Selected Approach: Modern Stack (ruff + mypy + pytest)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.x
    hooks:
      - id: ruff-check
        args: [--fix]
        exclude: alembic/versions/
      - id: ruff-format
        exclude: alembic/versions/
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.x.x
    hooks:
      - id: mypy
        exclude: alembic/versions/
        additional_dependencies: [types-all]
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

### Why This Approach:
- **ruff-check**: Linting (replaces Flake8) with auto-fix
- **ruff-format**: Code formatting (replaces Black + isort)
- **mypy**: Type checking for better code quality
- **pytest**: Run tests to ensure functionality works

## Testing Hooks
- Basic functionality tests
- Performance impact assessment
- Integration with existing workflows
- Error handling and user experience

## Expected Outcomes
- Automatic code quality enforcement
- Consistent formatting across all commits
- Prevention of broken code entering repository
- Improved developer workflow with fast feedback
- Foundation for CI/CD pipeline (MAT-13)

## Files to be Created/Modified
- `.pre-commit-config.yaml` (new)
- Backend working directory for hook execution
- Potential updates to existing scripts for consistency

## Dependencies
- ✅ MAT-11 (linting/formatting tools configured)
- Pre-requisite for MAT-13 (CI/CD pipeline)

## Testing Strategy
1. **Clean Repository Test**: Hooks pass on clean code
2. **Dirty Repository Test**: Hooks catch and fix/block issues  
3. **Bypass Test**: Verify `--no-verify` option works for emergencies
4. **Performance Test**: Ensure hooks complete in reasonable time (ruff is much faster than Flake8)
5. **Integration Test**: Verify with existing development workflow and MAT-11 tools

## Risk Mitigation
- Provide bypass mechanism for emergency commits
- Ensure hooks are not too slow (< 30 seconds)
- Clear error messages for developers
- Documentation for setup and troubleshooting