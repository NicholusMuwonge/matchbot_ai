import logging

import redis
from redis.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Singleton Redis client with connection pooling.

    Maintains 5 persistent connections for efficient reuse.
    """

    _pool: ConnectionPool | None = None
    _client: redis.Redis | None = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get Redis client with connection pooling.

        Connection pool maintains 5 connections by default.
        decode_responses=False for binary data (file content).

        Returns:
            Redis client instance
        """
        if cls._client is None:
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=5,
                decode_responses=False,
            )
            cls._client = redis.Redis(connection_pool=cls._pool)
            logger.info(
                "Redis client initialized with connection pool (max_connections=5)"
            )
        return cls._client

    @classmethod
    def close(cls):
        """Close Redis connection pool on application shutdown."""
        if cls._pool:
            cls._pool.disconnect()
            cls._pool = None
            cls._client = None
            logger.info("Redis connection pool closed")


redis_client = RedisClient.get_client()
