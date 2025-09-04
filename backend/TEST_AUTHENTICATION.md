# Test Authentication System

## Overview

This system allows testing RBAC-protected endpoints without using Clerk API calls, avoiding billing consumption during development and testing.

## Quick Setup

### 1. Enable Test Authentication
```bash
export ENABLE_AUTH_TESTING=true
# Or add to your .env file:
echo "ENABLE_AUTH_TESTING=true" >> .env
```

### 2. Start FastAPI Server
```bash
uvicorn app.main:app --reload
```

You should see:
```
🧪 TEST AUTHENTICATION ENABLED
   Use X-Test-Role header: regular_user, platform_admin, or app_owner
   Call POST /api/v1/dev/setup-test-users to create test users
```

### 3. Setup Test Users
```bash
curl -X POST http://localhost:8000/api/v1/dev/setup-test-users
```

Or visit: http://localhost:8000/docs and call the `/dev/setup-test-users` endpoint

## Testing in Swagger UI

### Step 1: Open Swagger UI
Navigate to: http://localhost:8000/docs

### Step 2: Add Custom Headers
For each request you want to test, add the header:
- **Header Name**: `X-Test-Role`
- **Header Value**: One of:
  - `regular_user` - For regular user endpoints
  - `platform_admin` - For admin endpoints  
  - `app_owner` - For owner-only endpoints

### Step 3: Test Different Scenarios

**Test Regular User Access:**
```
X-Test-Role: regular_user
→ Try GET /items/ (should work)
→ Try GET /items/admin/all (should get 403)
```

**Test Admin Access:**
```
X-Test-Role: platform_admin
→ Try GET /items/admin/all (should work)
→ Try POST /admin/rbac/users/assign-role (should work)
```

**Test Owner Access:**
```
X-Test-Role: app_owner
→ Try DELETE /admin/rbac/users/{id}/roles/{role} (should work)
→ All admin endpoints should work
```

## Test Users Created

| Role | Email | Usage |
|------|-------|--------|
| `regular_user` | test-regular@example.com | Basic user endpoints |
| `platform_admin` | test-admin@example.com | Admin endpoints |
| `app_owner` | test-owner@example.com | All endpoints |

## API Testing with curl

```bash
# Test regular user endpoint
curl -H "X-Test-Role: regular_user" \
     http://localhost:8000/api/v1/items/

# Test admin endpoint (should fail with regular_user)
curl -H "X-Test-Role: regular_user" \
     http://localhost:8000/api/v1/items/admin/all

# Test admin endpoint (should work with platform_admin)
curl -H "X-Test-Role: platform_admin" \
     http://localhost:8000/api/v1/items/admin/all
```

## How It Works

1. **Dependency Override**: When `ENABLE_AUTH_TESTING=true`, FastAPI replaces the real Clerk authentication with mock authentication
2. **Header-Based Role Selection**: The `X-Test-Role` header determines which test user to authenticate as
3. **Real Database Users**: Test users are created in your actual database with proper RBAC roles assigned
4. **Zero Clerk API Usage**: No calls to Clerk API, preventing billing consumption

## Important Notes

- **Only for Development**: Never enable in production (`ENABLE_AUTH_TESTING=false` by default)
- **Real Database**: Test users are created in your actual database
- **CORS Enabled**: The `X-Test-Role` header is allowed in CORS configuration
- **Full RBAC**: All role-based permissions work exactly as in production

## Disable Test Authentication

```bash
export ENABLE_AUTH_TESTING=false
# Or remove from .env file
```

Restart the server - it will use normal Clerk authentication.