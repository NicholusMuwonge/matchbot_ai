# Branch Protection Setup Guide

This document outlines the branch protection rules that should be configured for the matchbot_ai repository to enforce code quality and review processes.

## Prerequisites

- Repository admin access
- GitHub CLI authenticated or web access to GitHub repository settings

## Branch Protection Rules

### Main Branch Protection

Configure the following rules for the `main` branch:

1. **Require pull request reviews before merging**
   - Required number of reviewers: 1
   - Dismiss stale reviews when new commits are pushed: ✓
   - Require review from code owners: ✓ (if CODEOWNERS file exists)

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✓
   - Status checks to require:
     - `ci` (GitHub Actions CI workflow)
     - `lint-backend` (Backend linting)
     - `test-backend` (Backend tests)
     - `playwright` (E2E tests, when implemented)

3. **Require conversation resolution before merging**: ✓

4. **Require signed commits**: ✓ (recommended for security)

5. **Include administrators**: ✓ (enforce rules for all users including admins)

6. **Restrict pushes that create files**: ✗ (allow file creation)

7. **Allow force pushes**: ✗ (prevent force pushes to main)

8. **Allow deletions**: ✗ (prevent branch deletion)

### Develop Branch Protection

Configure the following rules for the `develop` branch:

1. **Require pull request reviews before merging**
   - Required number of reviewers: 1
   - Dismiss stale reviews when new commits are pushed: ✓

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✓
   - Status checks to require:
     - `ci` (GitHub Actions CI workflow)
     - `lint-backend` (Backend linting)
     - `test-backend` (Backend tests)

3. **Require conversation resolution before merging**: ✓

4. **Include administrators**: ✓

5. **Allow force pushes**: ✗

6. **Allow deletions**: ✗

## Setup Instructions

### Option 1: GitHub Web Interface

1. Go to your repository: https://github.com/NicholusMuwonge/matchbot_ai
2. Click "Settings" tab
3. Click "Branches" in the left sidebar
4. Click "Add rule" or "Edit" for existing rules
5. Configure the rules as specified above for each branch

### Option 2: GitHub CLI (when authentication is working)

```bash
# Enable branch protection for main
gh api repos/NicholusMuwonge/matchbot_ai/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci","lint-backend","test-backend"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false

# Enable branch protection for develop
gh api repos/NicholusMuwonge/matchbot_ai/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci","lint-backend","test-backend"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

## Verification

After setting up branch protection rules:

1. Try to push directly to `main` or `develop` - should be blocked
2. Create a PR from a feature branch to `develop`
3. Verify that status checks are required before merge
4. Verify that at least 1 review is required before merge

## Workflow

With these rules in place, the development workflow should be:

1. `main` → `develop` → `feature_branch`
2. Work on `feature_branch`
3. Create PR: `feature_branch` → `develop`
4. After review and CI passes, merge to `develop`
5. Periodically create PR: `develop` → `main` for releases
6. After review and CI passes, merge to `main`

## Notes

- The status check names (ci, lint-backend, test-backend, etc.) must match exactly with the job names in your GitHub Actions workflows
- If you don't have certain status checks yet, you can add them to the protection rules later
- Consider adding CODEOWNERS file for automatic review assignment