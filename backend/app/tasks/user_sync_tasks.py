"""
Celery tasks for user synchronization operations
Run user sync operations in background to avoid blocking main thread
"""

from typing import Any

from app.core.celery import celery_app
from app.services.clerk_auth import ClerkAuthenticationError
from app.services.user_sync_service import UserSyncError, UserSyncService


@celery_app.task(
    bind=True,
    autoretry_for=(UserSyncError, ClerkAuthenticationError),
    retry_kwargs={"max_retries": 3, "countdown": 60},  # Retry 3 times with 60s delay
    time_limit=300,  # 5 minutes
    soft_time_limit=240,  # 4 minutes
)
def sync_user_from_clerk_task(self, clerk_user_data: dict[str, Any]) -> dict[str, Any]:
    """Background task to sync user from Clerk webhook data"""
    try:
        # Create sync service instance
        sync_service = UserSyncService()

        # Run sync operation synchronously in background
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                sync_service.sync_user_from_clerk(clerk_user_data)
            )
            return result
        finally:
            loop.close()

    except UserSyncError as e:
        # Log error and potentially retry
        self.retry(countdown=60, exc=e)
    except Exception as e:
        # For other exceptions, don't retry
        raise UserSyncError(f"Unexpected error in user sync task: {str(e)}")


@celery_app.task(
    bind=True,
    autoretry_for=(UserSyncError, ClerkAuthenticationError),
    retry_kwargs={"max_retries": 2, "countdown": 120},  # Retry 2 times with 2m delay
    time_limit=600,  # 10 minutes (API calls can be slow)
    soft_time_limit=540,  # 9 minutes
)
def fetch_and_sync_user_task(self, clerk_user_id: str) -> dict[str, Any]:
    """Background task to fetch user from Clerk API and sync to local DB"""
    try:
        from app.services.clerk_auth import ClerkService

        clerk_service = ClerkService()
        sync_service = UserSyncService()

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            clerk_data = loop.run_until_complete(clerk_service.get_user(clerk_user_id))

            if not clerk_data:
                return {
                    "status": "not_found",
                    "clerk_user_id": clerk_user_id,
                    "message": "User not found in Clerk",
                }

            result = loop.run_until_complete(
                sync_service.sync_user_from_clerk(clerk_data)
            )
            return result

        finally:
            loop.close()

    except (UserSyncError, ClerkAuthenticationError) as e:
        # Retry on expected errors
        self.retry(countdown=120, exc=e)
    except Exception as e:
        # Don't retry on unexpected errors
        raise UserSyncError(f"Unexpected error in fetch and sync task: {str(e)}")


@celery_app.task(
    bind=True,
    autoretry_for=(UserSyncError,),
    retry_kwargs={"max_retries": 1, "countdown": 30},  # Quick retry for delete
    time_limit=120,  # 2 minutes
    soft_time_limit=90,  # 1.5 minutes
)
def delete_user_task(self, clerk_user_id: str) -> dict[str, Any]:
    """Background task to soft delete user"""
    try:
        sync_service = UserSyncService()
        deleted = sync_service.delete_user_by_clerk_id(clerk_user_id)

        return {"status": "success", "clerk_user_id": clerk_user_id, "deleted": deleted}

    except UserSyncError as e:
        # Retry once on sync errors
        self.retry(countdown=30, exc=e)
    except Exception as e:
        # Don't retry on unexpected errors
        raise UserSyncError(f"Unexpected error in delete user task: {str(e)}")


@celery_app.task(
    bind=True,
    autoretry_for=(UserSyncError, ClerkAuthenticationError),
    retry_kwargs={"max_retries": 2, "countdown": 180},  # Retry with 3m delay
    time_limit=900,  # 15 minutes (can process multiple users)
    soft_time_limit=840,  # 14 minutes
)
def sync_user_by_email_task(self, email: str) -> dict[str, Any] | None:
    """Background task to find and sync user by email"""
    try:
        sync_service = UserSyncService()

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(sync_service.sync_user_by_email(email))
            return result

        finally:
            loop.close()

    except (UserSyncError, ClerkAuthenticationError) as e:
        # Retry on expected errors
        self.retry(countdown=180, exc=e)
    except Exception as e:
        # Don't retry on unexpected errors
        raise UserSyncError(f"Unexpected error in email sync task: {str(e)}")


@celery_app.task(
    time_limit=300,  # 5 minutes
    soft_time_limit=240,  # 4 minutes
)
def get_user_sync_stats_task() -> dict[str, int]:
    """Background task to get synchronization statistics"""
    try:
        sync_service = UserSyncService()
        return sync_service.get_sync_stats()

    except Exception as e:
        raise UserSyncError(f"Failed to get sync stats: {str(e)}")


# Task scheduling helpers
def schedule_user_sync(clerk_user_data: dict[str, Any], delay_seconds: int = 0) -> str:
    """Schedule user sync task with optional delay"""
    if delay_seconds > 0:
        task = sync_user_from_clerk_task.apply_async(
            args=[clerk_user_data], countdown=delay_seconds
        )
    else:
        task = sync_user_from_clerk_task.delay(clerk_user_data)

    return task.id


def schedule_user_fetch_and_sync(clerk_user_id: str, delay_seconds: int = 0) -> str:
    """Schedule fetch and sync task with optional delay"""
    if delay_seconds > 0:
        task = fetch_and_sync_user_task.apply_async(
            args=[clerk_user_id], countdown=delay_seconds
        )
    else:
        task = fetch_and_sync_user_task.delay(clerk_user_id)

    return task.id


def schedule_user_delete(clerk_user_id: str, delay_seconds: int = 0) -> str:
    """Schedule user deletion task with optional delay"""
    if delay_seconds > 0:
        task = delete_user_task.apply_async(
            args=[clerk_user_id], countdown=delay_seconds
        )
    else:
        task = delete_user_task.delay(clerk_user_id)

    return task.id
