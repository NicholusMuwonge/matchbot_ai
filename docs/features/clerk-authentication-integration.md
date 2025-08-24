# Clerk Authentication Integration Documentation

## Overview

This document provides comprehensive documentation for the Clerk authentication integration implemented in the matchbot_ai backend. Clerk is a complete user authentication and management platform that handles user sign-up, sign-in, profile management, and security features.

## Architecture Overview

The Clerk integration consists of several key components:

1. **ClerkService** - Core service for interacting with Clerk's backend API
2. **UserSyncService** - Handles synchronization between Clerk users and local database
3. **WebhookProcessor** - Processes Clerk webhooks for real-time user updates
4. **Background Tasks** - Celery tasks for asynchronous user operations
5. **Models** - Database models for storing Clerk-related data

## Core Services

### ClerkService (`app/services/clerk_service.py`)

The primary service for interacting with Clerk's backend API.

#### Features:
- **Session Token Validation** - Validates user session tokens
- **User Management** - Fetch and manage user data from Clerk
- **Webhook Signature Verification** - Secures webhook endpoints
- **Async/Sync Support** - Handles both synchronous and asynchronous operations

#### Key Methods:

```python
# Session validation
async def validate_session_token(session_token: str) -> Dict[str, Any]

# User retrieval
async def get_user(user_id: str) -> Optional[Dict[str, Any]]

# User listing with filters
async def list_users(email_address: Optional[str] = None, limit: int = 10) -> Dict[str, Any]

# Webhook signature verification  
async def verify_webhook_signature(payload: str, headers: Dict[str, str]) -> bool
```

#### Configuration:
- `CLERK_SECRET_KEY` - Backend API key for authentication
- `CLERK_PUBLISHABLE_KEY` - Frontend publishable key
- `CLERK_WEBHOOK_SECRET` - Secret for webhook signature verification

### UserSyncService (`app/services/user_sync_service.py`)

Manages synchronization between Clerk users and the local database.

#### Features:
- **Bi-directional Sync** - Sync users from Clerk to local DB and vice versa
- **Conflict Resolution** - Handles duplicate users and email conflicts
- **User State Management** - Tracks sync status and provider information
- **Statistics & Monitoring** - Provides sync statistics and health metrics

#### Key Methods:

```python
# Sync user from Clerk webhook data
async def sync_user_from_clerk(clerk_data: Dict[str, Any]) -> Dict[str, Any]

# Fetch user from Clerk API and sync to local DB
async def fetch_and_sync_user(clerk_user_id: str) -> Dict[str, Any]

# Find and sync user by email
async def sync_user_by_email(email: str) -> Optional[Dict[str, Any]]

# Soft delete user (mark as inactive)
def delete_user_by_clerk_id(clerk_user_id: str) -> bool

# Get synchronization statistics
def get_sync_stats() -> Dict[str, int]
```

#### User Data Fields:
- `clerk_user_id` - Unique Clerk user identifier
- `auth_provider` - Authentication provider ("clerk")
- `is_synced` - Synchronization status
- `email_verified` - Email verification status
- `profile_image_url` - User's profile image
- `first_name`, `last_name`, `full_name` - User name fields

### WebhookProcessor (`app/webhooks/clerk_webhooks.py`)

Processes real-time webhooks from Clerk for user lifecycle events.

#### Features:
- **Event Processing** - Handles user.created, user.updated, user.deleted events
- **Signature Verification** - Validates webhook authenticity
- **Retry Logic** - Implements exponential backoff for failed webhooks
- **Idempotency** - Prevents duplicate processing of the same webhook
- **State Machine** - Tracks webhook processing states

#### Supported Events:
- `user.created` - New user registration
- `user.updated` - User profile changes
- `user.deleted` - User account deletion

#### Webhook States:
- `pending` - Webhook received, awaiting processing
- `processing` - Currently being processed
- `success` - Successfully processed
- `failed` - Processing failed (will retry)
- `invalid` - Invalid signature or payload
- `ignored` - Event type not supported

### Background Tasks (`app/tasks/user_sync_tasks.py`)

Celery tasks for asynchronous user operations to avoid blocking the main thread.

#### Available Tasks:

```python
# Sync user from webhook data
@celery_app.task
def sync_user_from_clerk_task(clerk_user_data: Dict[str, Any]) -> Dict[str, Any]

# Fetch user from Clerk API and sync
@celery_app.task  
def fetch_and_sync_user_task(clerk_user_id: str) -> Dict[str, Any]

# Soft delete user
@celery_app.task
def delete_user_task(clerk_user_id: str) -> Dict[str, Any]

# Sync user by email
@celery_app.task
def sync_user_by_email_task(email: str) -> Optional[Dict[str, Any]]

# Get sync statistics
@celery_app.task
def get_user_sync_stats_task() -> Dict[str, int]
```

#### Task Configuration:
- **Retry Logic** - Automatic retries with exponential backoff
- **Time Limits** - Configurable soft and hard time limits
- **Error Handling** - Specific error types trigger different retry behaviors

## Database Models

### User Model Extensions
```python
class User(UserBase, table=True):
    # Existing fields...
    
    # Clerk integration fields
    clerk_user_id: Optional[str] = Field(default=None, unique=True, index=True)
    auth_provider: str = Field(default="local")  # "clerk" | "local"
    is_synced: bool = Field(default=False)
    email_verified: bool = Field(default=False)
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)
    profile_image_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)
```

### WebhookEvent Model
```python
class WebhookEvent(SQLModel, table=True):
    id: int = Field(primary_key=True)
    webhook_id: str = Field(unique=True, index=True)
    event_type: str = Field(index=True)
    status: WebhookStatus = Field(default=WebhookStatus.PENDING)
    
    # Processing metadata
    processed_at: Optional[datetime] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    next_retry_at: Optional[datetime] = None
    
    # Data and error tracking
    raw_data: dict = Field(sa_column=Column(JSON))
    processed_data: Optional[dict] = Field(default=None)
    error_message: Optional[str] = None
    error_details: Optional[dict] = Field(default=None)
    
    # Request metadata
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## Integration Workflow

### User Registration Flow
1. User registers through Clerk frontend
2. Clerk sends `user.created` webhook
3. Webhook processor validates signature
4. Background task syncs user to local database
5. User profile is available in both Clerk and local DB

### User Update Flow
1. User updates profile in Clerk
2. Clerk sends `user.updated` webhook
3. Background task updates local user record
4. Changes are reflected in local database

### User Deletion Flow
1. User deletes account in Clerk
2. Clerk sends `user.deleted` webhook
3. Background task marks local user as inactive
4. User can no longer access the system

## Configuration

### Environment Variables
```env
# Required
CLERK_SECRET_KEY=sk_test_...           # Backend API key
CLERK_PUBLISHABLE_KEY=pk_test_...      # Frontend publishable key
CLERK_WEBHOOK_SECRET=whsec_...         # Webhook signing secret

# Optional
REDIS_URL=redis://localhost:6379      # For Celery background tasks
```

### Settings Configuration
```python
# app/core/config.py
class Settings(BaseSettings):
    CLERK_SECRET_KEY: str = Field(default="", description="Clerk secret key")
    CLERK_PUBLISHABLE_KEY: str = Field(default="", description="Clerk publishable key") 
    CLERK_WEBHOOK_SECRET: str = Field(default="", description="Clerk webhook secret")
```

## Security Considerations

### Webhook Security
- All webhooks are verified using SVIX signature verification
- Timestamps are checked to prevent replay attacks
- Failed signature verification results in rejected webhooks

### API Security
- All Clerk API calls use the secret key for authentication
- Session tokens are validated before user operations
- User data is sanitized before database storage

### Data Privacy
- Sensitive user data is stored securely in the local database
- Profile images are linked, not stored locally
- Email verification status is tracked for compliance

## Error Handling & Monitoring

### Retry Logic
- Webhooks: Exponential backoff (2^retry_count minutes, max 60 minutes)
- User sync tasks: 3 retries with 60-second intervals
- API calls: 2 retries with 120-second intervals

### Logging & Monitoring
- All webhook events are logged with processing status
- Failed operations include detailed error messages
- Sync statistics are available for monitoring

### Health Checks
```python
# Get sync statistics
stats = UserSyncService().get_sync_stats()
# Returns: {
#     "total_users": 150,
#     "synced_users": 140,
#     "unsynced_users": 10,
#     "active_users": 145,
#     "clerk_users": 140
# }
```

## Testing

The integration includes comprehensive test coverage:

### Service Tests (`app/tests/services/test_clerk_service.py`)
- Mock Clerk API responses
- Test authentication flows
- Validate error handling

### Webhook Tests (`app/tests/webhooks/`)
- Test webhook signature verification
- Validate event processing logic
- Test retry mechanisms

### Integration Tests (`app/tests/models/`)
- End-to-end user sync flows
- Database consistency checks
- State machine validation

## Migration & Deployment

### Database Migration
```python
# Migration adds Clerk fields to User model
def upgrade():
    op.add_column('user', sa.Column('clerk_user_id', sa.String(), nullable=True))
    op.add_column('user', sa.Column('auth_provider', sa.String(), nullable=False, default='local'))
    op.add_column('user', sa.Column('is_synced', sa.Boolean(), nullable=False, default=False))
    # ... additional fields
    
    op.create_index('ix_user_clerk_user_id', 'user', ['clerk_user_id'], unique=True)
```

### Deployment Checklist
1. Set up Clerk application in dashboard
2. Configure environment variables
3. Run database migrations
4. Set up webhook endpoints in Clerk dashboard
5. Configure Celery workers for background tasks
6. Test webhook delivery and processing

## Troubleshooting

### Common Issues

1. **Webhook Signature Verification Fails**
   - Check `CLERK_WEBHOOK_SECRET` is correct
   - Verify webhook endpoint URL in Clerk dashboard
   - Check server clock synchronization

2. **User Sync Not Working**
   - Verify Celery workers are running
   - Check Redis connection for task queue
   - Review error logs in webhook events table

3. **Duplicate Users**
   - Check email uniqueness constraints
   - Review user conflict resolution logic
   - Verify Clerk user ID mapping

4. **API Authentication Errors**
   - Verify `CLERK_SECRET_KEY` is valid
   - Check API key permissions in Clerk dashboard
   - Review rate limiting and quotas

### Debug Commands
```bash
# Check Celery worker status
celery -A app.core.celery worker --loglevel=info

# Monitor webhook events
SELECT * FROM webhook_events WHERE status = 'failed' ORDER BY created_at DESC;

# Check user sync status
SELECT auth_provider, is_synced, COUNT(*) FROM users GROUP BY auth_provider, is_synced;
```

## Future Enhancements

### Planned Features
1. **Role-Based Access Control** - Integrate Clerk organizations and roles
2. **Multi-Factor Authentication** - Support for MFA flows
3. **Social Providers** - Enhanced OAuth provider support
4. **User Analytics** - Track user engagement and authentication metrics
5. **Bulk Operations** - Mass user import/export capabilities

### API Extensions
1. **GraphQL Support** - Add GraphQL endpoints for user operations
2. **Real-time Events** - WebSocket support for user status changes
3. **Advanced Filtering** - Enhanced user search and filtering capabilities

## Support & Resources

- [Clerk Documentation](https://docs.clerk.dev/)
- [Clerk Backend API Reference](https://docs.clerk.dev/reference/backend-api)
- [Webhook Event Reference](https://docs.clerk.dev/webhooks/event-types)
- [SVIX Webhook Verification](https://docs.svix.com/receiving/verifying-payloads/python)