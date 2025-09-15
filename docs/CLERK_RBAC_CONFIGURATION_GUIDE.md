# MatchBot AI RBAC Implementation Guide (Simplified)

## Executive Summary

A simple, backend-first RBAC system where:
- **Backend owns roles & permissions** (database-driven, dynamic)
- **Clerk handles authentication** (user management, login, sessions)
- **Webhooks sync everything** (automatic role assignment)
- **Metadata stores role name only** (for session claims)

### Design Principles
1. **Simplicity First**: Backend is source of truth
2. **Dynamic Roles**: Add/remove roles without code changes
3. **Webhook-Driven**: Automatic sync on user events
4. **Free Tier Compatible**: Uses Clerk metadata, no custom roles

## System Architecture

### Simple Flow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Clerk Frontend │────▶│  Clerk Webhooks  │────▶│  Python Backend │
│  (User SignUp)  │     │  (user.created)  │     │  (Sync & Role) │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │  Database       │
                                                  │  - users        │
                                                  │  - roles        │
                                                  │  - permissions  │
                                                  └─────────────────┘

1. User signs up via Clerk component (frontend handles everything)
2. Webhook fires to backend
3. Backend syncs user, assigns role
4. Backend updates Clerk metadata with role name
5. Role name available in session claims
```

### Backend Role Management

```python
# Backend Database Schema (simplified)
roles_table:
  - id: UUID
  - name: str (e.g., "app_owner", "admin", "regular_user")
  - permissions: JSON (list of permission strings)
  - created_at: datetime

user_roles_table:
  - user_id: UUID
  - role_id: UUID
  - assigned_at: datetime

# When user.created webhook fires:
def process_user_created(clerk_data):
    # 1. Sync user to database
    user = create_or_update_user(clerk_data)
    
    # 2. Assign default role
    role = get_role_by_name("regular_user")
    assign_role_to_user(user, role)
    
    # 3. Update Clerk metadata (role name only!)
    clerk_client.update_user_metadata(user.clerk_id, {
        "publicMetadata": {"role": role.name}
    })
```

### What Goes Where?

| Data Type | Backend DB | Clerk Metadata | Session Claims |
|-----------|------------|----------------|----------------|
| Role Definitions | ✅ Full details | ❌ | ❌ |
| Permissions | ✅ Full list | ❌ | ❌ |
| User's Role Name | ✅ | ✅ publicMetadata | ✅ |
| App Owner Flag | ✅ | ✅ publicMetadata | ✅ |
| Billing Tier | ✅ | ✅ org.publicMetadata | ✅ |

**Key Insight**: Only the role NAME goes to Clerk. Permissions stay in backend.

## Session Token Configuration

Navigate to: Clerk Dashboard → Sessions → Edit session token

```json
{
  "role": "{{user.public_metadata.role}}",
  "isAppOwner": "{{user.public_metadata.isAppOwner}}",
  "billingTier": "{{org.public_metadata.billingTier}}"
}
```

That's it! Just the role name, not permissions.

## Implementation Steps

### Step 1: Backend Database Setup

```python
# models.py
from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(UUID, primary_key=True)
    name = Column(String, unique=True)  # e.g., "app_owner", "admin"
    permissions = Column(JSON)  # ["users:read", "users:write", ...]
    
class UserRole(Base):
    __tablename__ = 'user_roles'
    
    user_id = Column(UUID, ForeignKey('users.id'))
    role_id = Column(UUID, ForeignKey('roles.id'))
    assigned_at = Column(DateTime)

# Seed initial roles
def seed_roles():
    roles = [
        {"name": "app_owner", "permissions": ["*"]},
        {"name": "platform_admin", "permissions": ["users:*", "analytics:*"]},
        {"name": "support_admin", "permissions": ["users:read", "tickets:*"]},
        {"name": "regular_user", "permissions": ["profile:read", "profile:write"]}
    ]
    # Insert into database
```

### Step 2: Update Webhook Handler

```python
# clerk_webhooks.py
from clerk import Client
clerk_client = Client(api_key=CLERK_SECRET_KEY)

async def _process_user_created(self, user_data: dict) -> dict:
    """Enhanced webhook handler with role assignment"""
    
    # 1. Sync user to database
    clerk_user_id = user_data.get("id")
    user = await self.user_sync_service.sync_user_from_clerk(user_data)
    
    # 2. Determine and assign role
    role = await self.determine_user_role(user_data)
    await self.assign_role_to_user(user.id, role.id)
    
    # 3. Update Clerk metadata with role name
    await clerk_client.users.update_user_metadata(
        clerk_user_id,
        public_metadata={"role": role.name}
    )
    
    return {
        "status": "success",
        "user_id": user.id,
        "role_assigned": role.name
    }

async def determine_user_role(self, user_data: dict) -> Role:
    """Determine role based on business logic - role-only approach"""
    
    # Default role assignment - all users get regular_user initially
    # App owner and admin roles are assigned manually through:
    # 1. Direct database updates, or
    # 2. Admin panel role assignment (to be built)
    return get_role_by_name("regular_user")
```

### Step 3: Authorization in Backend

```python
# auth.py
from functools import wraps
from fastapi import HTTPException

def require_permission(permission: str):
    """Decorator to check permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Get role from session claims (fast!)
            role_name = request.auth.session_claims.get("role")
            
            # Special case: app owner can do anything
            if request.auth.session_claims.get("isAppOwner"):
                return await func(request, *args, **kwargs)
            
            # Check permission in database
            role = get_role_by_name(role_name)
            if permission not in role.permissions and "*" not in role.permissions:
                raise HTTPException(403, "Insufficient permissions")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/api/admin/users")
@require_permission("users:write")
async def create_user(request):
    # Only users with users:write permission can access
    pass
```

### Step 4: Frontend Usage (Simple)

```typescript
// Frontend just reads the role from session
import { useAuth } from '@clerk/nextjs';

export function AdminPanel() {
  const { sessionClaims } = useAuth();
  const role = sessionClaims?.role;
  const isAppOwner = sessionClaims?.isAppOwner;
  
  // Simple role check
  if (role !== 'admin' && !isAppOwner) {
    return <div>Access Denied</div>;
  }
  
  return <div>Admin Content</div>;
}

// That's it! No complex permission logic in frontend
```

## Special Cases

### App Owner Setup (Manual Assignment)

Since we only rely on roles (not email verification), app owner assignment is manual:

**Option 1: Clerk Dashboard (Quick)**
1. Go to Clerk Dashboard → Users → Your User
2. Edit Metadata → Public Metadata:
```json
{
  "role": "app_owner",
  "isAppOwner": true
}
```

**Option 2: Database + Metadata Sync (Preferred)**
1. Update user role in database to `app_owner`
2. Sync metadata to Clerk using admin API
3. Ensures database and Clerk stay in sync

### Admin User Creation

Since we don't rely on email-based assignment:
1. User signs up normally (gets `regular_user` role via webhook)
2. Manually promote to admin through:
   - Database role update + metadata sync, or
   - Admin panel role assignment (to be built), or
   - Direct Clerk Dashboard metadata update

### Organizations (Teams)

Clerk handles this automatically:
- User creates org → They become `org:admin`
- User invites member → They become `org:member`
- These are separate from your custom roles

## Dynamic Role Management

### Adding New Roles (No Code Changes!)

```python
# Just insert into database
new_role = Role(
    name="content_moderator",
    permissions=["content:read", "content:delete", "users:ban"]
)
db.session.add(new_role)
db.session.commit()

# That's it! The role is now available
```

### Changing Permissions

```python
# Just update the database
role = get_role_by_name("support_admin")
role.permissions.append("billing:view")
db.session.commit()

# Immediately effective on next request
```

## Implementation Task Breakdown

### Phase 0: Branch Strategy Setup

**Tasks I'll handle:**
- [ ] Create major feature branch `feature/rbac-implementation` from develop branch
- [ ] Push feature branch to remote
- [ ] Create draft MR from `feature/rbac-implementation` to `develop` for tracking overall progress

**Tasks for you:**
- [ ] Review and approve the draft MR setup for visibility into overall progress

**Branch Strategy for Individual Tasks:**
- Each phase task will create its own branch from `feature/rbac-implementation`
- Small MRs will be created from task branches to `feature/rbac-implementation` 
- After all phases complete, final MR from `feature/rbac-implementation` to `develop`

**Example Branch Flow:**
```
develop
  ↳ feature/rbac-implementation (major feature branch)
    ↳ feature/rbac-database-setup (Phase 1)
    ↳ feature/rbac-backend-integration (Phase 2)
    ↳ feature/rbac-clerk-config (Phase 3)
    ↳ feature/rbac-frontend-integration (Phase 4)
    ↳ feature/rbac-testing (Phase 5)
```

---

### Phase 1: Database Setup (Backend) ✅ COMPLETED

**Tasks I handled:**
- [x] Create database migration for roles and user_roles tables (with JSONB permissions)
- [x] Create Role and UserRole models with relationships  
- [x] Add role service functions for CRUD operations
- [x] Create database seeder for initial roles (app_owner, admin, regular_user)
- [x] Update imports in models/__init__.py to include RBAC models
- [x] Reorganize seeders into dedicated app/seeders/ directory
- [x] Create comprehensive test suite with Ruby → Python guide

**Tasks for you:**
- [x] Run the database migration after I create it
- [x] Verify database tables are created correctly

---

### Phase 2: Backend RBAC Integration ✅ COMPLETE

**✅ COMPLETED - Core Services:**
- [x] Create RoleAssignmentService with business logic
- [x] Create enhanced webhook processor 
- [x] Create comprehensive test file with TDD approach
- [x] Implement `get_primary_email()` method in RoleAssignmentService
- [x] Implement `determine_user_role()` method (supports all role types)
- [x] Implement `assign_initial_role()` method with full functionality
- [x] Complete all tests in test_role_assignment_service.py (comprehensive suite)
- [x] Implement `update_clerk_user_metadata()` in enhanced webhook processor
- [x] Implement `_get_user_by_clerk_id()` helper method
- [x] Connect enhanced processor to main webhook handler

**✅ COMPLETED - API & Authorization:**
- [x] Create FastAPI dependency system (require_permission, require_role)
- [x] Create admin API endpoints for role management (/admin/rbac/)
- [x] Refactor all routes to use proper RBAC dependencies
- [x] Create clean type aliases (AdminUser, AppOwnerUser, PlatformAdminUser)
- [x] Implement role-based route protection across entire API

**✅ COMPLETED - Testing & Documentation:**
- [x] Write comprehensive unit tests for deps.py (require_role, require_permission functions)
- [x] Create test authentication system for Swagger testing (bypasses Clerk billing)
- [x] Complete documentation with setup guides

**📁 FILES CREATED/MODIFIED:**
- `backend/app/services/role_assignment_service.py` (185 lines) - Role assignment business logic
- `backend/app/webhooks/enhanced_clerk_webhooks.py` (78 lines) - Enhanced webhook processor
- `backend/tests/services/test_role_assignment_service.py` (329 lines) - TDD test suite
- `backend/tests/api/test_deps.py` (340 lines) - Authentication/authorization tests  
- `backend/app/api/deps.py` (148 lines) - FastAPI dependency injection system
- `backend/app/api/routes/admin/rbac.py` (237 lines) - RBAC admin API
- `backend/app/api/routes/admin/clerk.py` (156 lines) - Clerk admin API (refactored)
- `backend/app/api/routes/items.py` (172 lines) - User/admin endpoints (refactored)
- `backend/app/api/routes/users.py` (347 lines) - User management (refactored)
- `backend/app/api/test_auth.py` (123 lines) - Test authentication system
- `backend/app/api/routes/dev.py` (67 lines) - Development testing endpoints
- `backend/app/core/config.py` (updated) - Added ENABLE_AUTH_TESTING setting
- `backend/app/main.py` (updated) - Dependency override for testing
- `backend/TEST_AUTHENTICATION.md` (documentation) - Testing guide

**🎯 PHASE 2 ACHIEVEMENTS:**
- **Full RBAC System**: Complete role-based access control with 3 roles
- **Production-Ready APIs**: Admin endpoints for role management
- **Comprehensive Testing**: 669 lines of test code with full coverage
- **Test Authentication**: Swagger testing without Clerk billing
- **Clean Architecture**: FastAPI dependency injection best practices

---

### Phase 3: Clerk Configuration

**Tasks for you (Clerk Dashboard):**
- [ ] Configure session token to include role claims: `{"role": "{{user.public_metadata.role}}", "isAppOwner": "{{user.public_metadata.isAppOwner}}"}`
- [ ] Set your user as app_owner in public metadata manually
- [ ] Test that session claims are working in frontend

**Tasks I'll handle:**
- [ ] Document exact steps for Clerk configuration
- [ ] Create verification script to test session claims

---

### Phase 4: Frontend Integration (Simple)

**Tasks I'll handle:**
- [ ] Create simple auth hook for reading role from session claims
- [ ] Create role guard component for protecting routes/components
- [ ] Update UserMenu component to show role-based options

**Tasks for you:**
- [ ] Test frontend auth components after implementation
- [ ] Apply role guards to admin sections
- [ ] Verify role display in user interface

---

### Phase 5: Testing & Validation

**Tasks I'll handle:**
- [ ] Create test script for role assignment workflow
- [ ] Add error handling for role assignment failures
- [ ] Create debugging utilities for RBAC issues

**Tasks for you:**
- [ ] Test complete flow: signup → webhook → role assignment → frontend display
- [ ] Test permission enforcement on API routes
- [ ] Verify app owner override functionality

---

### Phase 6: Documentation & Cleanup

**Tasks I'll handle:**
- [ ] Update API documentation with new auth decorators
- [ ] Create troubleshooting guide for common RBAC issues
- [ ] Clean up unused auth-related files

**Tasks for you:**
- [ ] Document any custom role assignment rules for your use case
- [ ] Set up monitoring/alerts for webhook failures
- [ ] Plan role expansion strategy for future needs

---

## Priority Order (What to tackle first)

1. **Phase 0 (Branch Setup)** - Create feature branch structure for organized development
2. **Phase 1 (Database)** - Foundation for everything else
3. **Phase 2 (Backend)** - Core RBAC logic  
4. **Phase 3 (Clerk Config)** - Critical for session claims to work
5. **Phase 4 (Frontend)** - Simple integration once backend is ready
6. **Phase 5 (Testing)** - Validation that everything works
7. **Phase 6 (Documentation)** - Polish and maintenance

## Estimated Timeline

- **Total time:** 4-6 hours split between us
- **My work:** ~3 hours (mostly backend implementation)
- **Your work:** ~2 hours (configuration, testing, verification)
- **Can work in parallel:** Phases 1-2 (me) while you handle Phase 3 (Clerk config)

## Dependencies

- **Phase 1 depends on Phase 0** (need feature branch setup first)
- **Phase 2 depends on Phase 1** (need database tables first)
- **Phase 4 depends on Phase 3** (need session claims configured)
- **Phase 5 depends on all previous phases** (need complete system)

Each individual task within a phase should be created as a separate branch from `feature/rbac-implementation` and merged back via small MRs for better code review and tracking.

This breakdown ensures we can work efficiently in parallel while maintaining clear ownership of tasks.


## Summary

This simplified RBAC system provides:

1. **Backend-First Design**: Database stores roles & permissions dynamically
2. **Webhook-Driven**: Automatic role assignment on user events
3. **Simple Metadata**: Only role name in Clerk, not complex permissions
4. **Free Tier Compatible**: Works without Clerk's paid custom roles
5. **Dynamic Management**: Add/remove roles without code changes

### Why This Approach?

- **Simplicity**: Backend owns everything, frontend just displays
- **Flexibility**: Change roles/permissions without deploying code
- **Performance**: Role name in session claims = fast checks
- **Maintainability**: Single source of truth (backend database)

### Key Points

- Frontend uses Clerk components for all auth UI (no custom code)
- Backend assigns roles via webhooks when users sign up
- Only role NAME goes to Clerk metadata (not permissions)
- Permissions checked in backend using database lookup
- App owner set manually in Clerk Dashboard (one-time)

### Future: Feature Flags (When Needed)

Feature flags will be a separate layer:
- Store in Redis/database (not in JWT)
- Check at runtime for A/B tests
- Update without touching RBAC
- Can be user-specific or org-specific

This approach keeps authentication (Clerk) separate from authorization (your backend), giving you full control while leveraging Clerk's excellent auth UI.