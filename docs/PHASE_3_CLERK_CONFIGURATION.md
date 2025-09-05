# Phase 3: Clerk Configuration Guide

## Overview

Phase 3 involves configuring Clerk Dashboard to include role information in session tokens and setting up initial app owner privileges.

## Step-by-Step Configuration

### 1. Configure Session Token Claims

**Location**: Clerk Dashboard → Sessions → Edit session token

**Steps**:
1. Navigate to your Clerk Dashboard
2. Go to "Sessions" in the sidebar
3. Click "Edit session token" 
4. Replace the default configuration with:

```json
{
  "role": "{{user.public_metadata.role}}",
  "isAppOwner": "{{user.public_metadata.isAppOwner}}"
}
```

**What this does**:
- Adds `role` claim to JWT tokens (e.g., "app_owner", "admin", "regular_user")
- Adds `isAppOwner` boolean claim for app owner override privileges
- These claims will be available in frontend via `useAuth().sessionClaims`

### 2. Set App Owner Privileges (Manual Setup)

Since automatic app owner detection is not implemented, you need to manually set your user as app owner.

**Option A: Clerk Dashboard (Recommended for initial setup)**

1. Navigate to Clerk Dashboard → Users
2. Find your user account
3. Click on your user
4. Go to "Metadata" tab
5. Edit "Public Metadata"
6. Add the following JSON:

```json
{
  "role": "app_owner",
  "isAppOwner": true
}
```

7. Save changes

**Option B: Database + API Sync (For production)**

This approach ensures database and Clerk stay synchronized:

1. Update database directly:
```sql
-- Find your user ID
SELECT id FROM users WHERE email = 'your-email@domain.com';

-- Assign app_owner role
INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u, roles r
WHERE u.email = 'your-email@domain.com' 
AND r.name = 'app_owner';
```

2. Sync to Clerk using backend API (future enhancement)

### 3. Verification Steps

After configuration, verify the setup works:

**A. Check Session Claims**

In your frontend console, run:
```javascript
import { useAuth } from '@clerk/nextjs';
const { sessionClaims } = useAuth();
console.log('Role:', sessionClaims?.role);
console.log('Is App Owner:', sessionClaims?.isAppOwner);
```

**B. Test API Endpoints**

Use the verification script (created in next step) to test backend authorization.

**C. Check Database Consistency**

Verify your user has the correct role in the database:
```sql
SELECT u.email, r.name as role_name 
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.email = 'your-email@domain.com';
```

## Expected Results

After successful configuration:

1. **Session Token**: Contains `role` and `isAppOwner` claims
2. **Frontend Access**: `sessionClaims.role` returns your role name
3. **API Access**: App owner can access all admin endpoints
4. **Database Sync**: User role matches Clerk metadata

## Troubleshooting

### Session Claims Not Appearing

**Symptom**: `sessionClaims.role` is undefined
**Solutions**:
1. Verify session token configuration is saved
2. Log out and log back in to refresh token
3. Check that public metadata is set correctly
4. Ensure no typos in metadata JSON

### Role Not Working in API

**Symptom**: Getting 403 Forbidden on admin endpoints
**Solutions**:
1. Verify webhook processed user creation properly
2. Check user exists in database with correct role
3. Confirm session claims include correct role
4. Test with verification script

### Webhook Issues

**Symptom**: User created but role not assigned
**Solutions**:
1. Check webhook endpoint is reachable
2. Verify webhook secret matches configuration
3. Check backend logs for webhook processing errors
4. Manually assign role if needed

## Manual Role Assignment (Temporary)

If webhook-based role assignment isn't working, you can manually assign roles:

### Via Clerk Dashboard
Update user's public metadata with desired role:
```json
{
  "role": "admin",
  "isAppOwner": false
}
```

### Via Database
Insert role assignment directly:
```sql
INSERT INTO user_roles (user_id, role_id, assigned_at)
SELECT u.id, r.id, NOW()
FROM users u, roles r
WHERE u.clerk_id = 'clerk_user_id_here'
AND r.name = 'admin';
```

Then sync metadata to Clerk (manual API call or update dashboard).

## Next Steps

After completing Phase 3 configuration:

1. **Test the verification script** (created in next step)
2. **Move to Phase 4**: Frontend integration
3. **Validate end-to-end flow**: Signup → Role Assignment → Frontend Display

## Configuration Summary

✅ **Session token configured** with role claims
✅ **App owner privileges set** in public metadata  
✅ **Verification completed** via console/API testing
✅ **Ready for Phase 4** frontend integration

This completes the Clerk configuration phase. The system now has:
- Role information in JWT tokens
- App owner override capabilities
- Manual role assignment capability
- Foundation for frontend role-based UI