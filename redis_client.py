"""
Redis Client for the LLM Document Intelligence System

This module provides a robust and asynchronous Redis client for caching,
session management, and real-time messaging. It encapsulates the logic for
connecting to Redis and performing common operations.

Key Features:
- Asynchronous client using redis-py's async support.
- Connection pooling for efficient connection management.
- Serialization and deserialization of complex Python objects.
- Methods for common Redis operations (get, set, delete, etc.).
"""

import asyncio
import json
import logging
import pickle
from typing import Any, Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError

from config import settings

logger = logging.getLogger(__name__)

class RedisService:
    """
    A service class for interacting with Redis. Manages the connection pool
    and provides methods for common Redis operations.
    """
    
    def __init__(self):
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        self._connection_lock = asyncio.Lock()
        
    async def connect(self):
        """
        Initializes the Redis connection pool and client.
        This method is thread-safe and ensures the connection is established only once.
        """
        async with self._connection_lock:
            if self.is_connected:
                return
            
            try:
                self.redis_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True  # Decode responses to strings by default
                )
                self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                await self.redis_client.ping()
                
                self.is_connected = True
                logger.info("Redis connection established successfully.")
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise ConnectionError(f"Redis connection failed: {e}")
    
    async def disconnect(self):
        """Closes the Redis connection and cleans up resources."""
        async with self._connection_lock:
            if not self.is_connected:
                return
            
            try:
                if self.redis_client:
                    await self.redis_client.close()
                if self.redis_pool:
                    await self.redis_pool.disconnect()
                
                self.is_connected = False
                logger.info("Redis connection closed successfully.")
                
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
    
    async def ping(self) -> bool:
        """Checks the health of the Redis connection."""
        if not self.is_connected or not self.redis_client:
            return False
        
        try:
            return await self.redis_client.ping()
        except Exception:
            return False

    def _serialize(self, value: Any) -> str:
        """Serializes a Python object to a string for storage in Redis."""
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value)
        return pickle.dumps(value).hex()

    def _deserialize(self, value: str) -> Any:
        """Deserializes a string from Redis back to a Python object."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            try:
                return pickle.loads(bytes.fromhex(value))
            except Exception:
                return value

    async def set(self, key: str, value: Any, expiration_seconds: Optional[int] = None):
        """
        Sets a key-value pair in Redis with an optional expiration time.

        Args:
            key: The key to set.
            value: The value to store (will be serialized).
            expiration_seconds: The time in seconds until the key expires.
        """
        if not self.is_connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_value = self._serialize(value)
            await self.redis_client.set(key, serialized_value, ex=expiration_seconds)
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a value from Redis by its key.

        Args:
            key: The key to retrieve.

        Returns:
            The deserialized Python object, or None if the key does not exist.
        """
        if not self.is_connected or not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            return self._deserialize(value) if value else None
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    async def delete(self, key: str):
        """Deletes a key from Redis."""
        if not self.is_connected or not self.redis_client:
            await self.connect()
            
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")

# --- Singleton Instance ---
# This ensures that only one instance of the service is used throughout the application.
redis_client = RedisService()