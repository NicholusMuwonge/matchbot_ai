# Claude Code Guidelines

## Branching Strategy
For each change you make, you must create a new branch. After implementing changes, push them up and create a merge request (MR) to the develop branch.

## Development Workflow
1. Create a new branch for your changes
2. Implement the required modifications
3. Push the branch to remote
4. Create a merge request targeting the develop branch

## Code Quality Standards
- Remove unnecessary comments (code should be self-documenting)
- Break down large functions into smaller, focused functions
- Single responsibility principle: each function does one thing well
- Use descriptive function and variable names
- Keep functions under 50 lines when possible

## 🚨 CRITICAL SECURITY GUIDELINES 🚨

### ABSOLUTELY FORBIDDEN - NEVER HARDCODE SECRETS
**⚠️ SECURITY VIOLATION DETECTED: Hardcoded Clerk secret key found in docker-compose.yml**
- NEVER hardcode API keys, tokens, or secrets directly in code files
- NEVER commit real API keys to version control (e.g., sk_test_*, sk_live_*, pk_test_*, pk_live_*)
- ALWAYS use environment variables for ALL sensitive configuration

### Environment Variable Requirements
- ALL secrets MUST use environment variable references: `${VAR_NAME}`
- Use `${VAR_NAME?Variable not set}` syntax in docker-compose.yml to enforce required variables
- NEVER put actual secret values in docker-compose.yml, only variable references

### Secret Patterns to Watch For
- Clerk Keys: `sk_test_*`, `sk_live_*`, `pk_test_*`, `pk_live_*`
- API Keys: `api_key`, `apikey`, `api-key`, `secret_key`
- Tokens: `access_token`, `auth_token`, `bearer`
- Cloud Credentials: `AWS_ACCESS_KEY`, `AWS_SECRET`, `GITHUB_TOKEN`
- Database Passwords: Never hardcode database credentials

### Best Practices
- NEVER commit .env, .env.local, .env.production files
- Always verify .env files are in .gitignore before first commit
- Use .env.example with placeholder values for documentation
- Rotate any accidentally exposed secrets IMMEDIATELY
- Scan codebase for secrets before every commit
- Review docker-compose.yml and configuration files for hardcoded values

### If Secrets Are Accidentally Exposed
1. Rotate the compromised credentials immediately
2. Remove the secret from version control history
3. Audit logs for any unauthorized access
4. Update all environments with new credentials