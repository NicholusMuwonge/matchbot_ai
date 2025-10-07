import logging
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.config import settings
from app.services.cache.redis_client import redis_client
from app.services.storage.minio_client import minio_client_service

if TYPE_CHECKING:
    from app.models.file import File

logger = logging.getLogger(__name__)


def get_cache_key(file_id: UUID | str) -> str:
    """Generate Redis cache key for file content."""
    return f"file_content:{file_id}"


def cache_file_content(file_id: UUID | str, content: bytes, ttl: int = 86400) -> bool:
    """
    Cache file content in Redis.

    Args:
        file_id: UUID of the file
        content: File content as bytes
        ttl: Time to live in seconds (default: 24 hours)

    Returns:
        True if cached successfully, False otherwise
    """
    cache_key = get_cache_key(file_id)

    try:
        redis_client.set(cache_key, content, ex=ttl)
        logger.info(
            f"Cached file {file_id} in Redis (TTL={ttl}s, size={len(content)} bytes)"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to cache file {file_id} in Redis: {e}")
        return False


def get_file_content(file: "File") -> bytes:
    """
    Get file content with lazy-loading cache pattern.

    Flow:
    1. Check Redis cache (hot path)
    2. If miss, load from MinIO (cold path)
    3. Cache in Redis for next time
    4. Return content

    Args:
        file: File instance with external_id and storage_path

    Returns:
        File content as bytes

    Raises:
        Exception: If file not found in MinIO
    """
    cache_key = get_cache_key(file.external_id)

    try:
        cached_content = redis_client.get(cache_key)
        if cached_content is not None:
            logger.info(f"Cache HIT for file {file.external_id}")
            return cached_content
    except Exception as e:
        logger.warning(f"Redis cache read failed for {file.external_id}: {e}")

    logger.info(f"Cache MISS for file {file.id}, loading from MinIO")
    try:
        file_stream = minio_client_service.get_object(
            bucket_name=settings.MINIO_BUCKET_RECONCILIATION,
            object_name=file.storage_path,
        )
        content = file_stream.read()

        cache_file_content(file.external_id, content)

        return content

    except Exception as e:
        logger.error(f"Failed to load file {file.external_id} from MinIO: {e}")
        raise


def invalidate_file_cache(file_id: UUID | str) -> bool:
    """
    Invalidate (delete) cached file content.

    Args:
        file_id: UUID of the file

    Returns:
        True if deleted, False if not found or error
    """
    cache_key = get_cache_key(file_id)

    try:
        deleted = redis_client.delete(cache_key)
        if deleted:
            logger.info(f"Invalidated cache for file {file_id}")
        return bool(deleted)
    except Exception as e:
        logger.error(f"Failed to invalidate cache for {file_id}: {e}")
        return False
