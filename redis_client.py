"""
Advanced Redis client with serialization for LLM Document Intelligence System.
Provides caching, session storage, and real-time data management.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Advanced Redis client with connection pooling and serialization."""
    
    def __init__(self):
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
        self._lock = asyncio.Lock()
        
    async def connect(self):
        """Initialize Redis connection with connection pooling."""
        async with self._lock:
            if self._connected:
                return
            
            try:
                # Create connection pool
                self.redis_pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    password=settings.REDIS_PASSWORD,
                    **settings.get_redis_config()
                )
                
                # Create Redis client
                self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                
                # Test connection
                await self.redis_client.ping()
                
                self._connected = True
                logger.info("Redis connection established successfully")
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise ConnectionError(f"Redis connection failed: {e}")
    
    async def disconnect(self):
        """Close Redis connection and cleanup resources."""
        async with self._lock:
            if not self._connected:
                return
            
            try:
                if self.redis_client:
                    await self.redis_client.close()
                
                if self.redis_pool:
                    await self.redis_pool.disconnect()
                
                self._connected = False
                logger.info("Redis connection closed successfully")
                
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
    
    async def ping(self) -> bool:
        """Check Redis connection health."""
        if not self._connected or not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode('utf-8')
        elif isinstance(value, (dict, list, tuple)):
            return json.dumps(value, default=str).encode('utf-8')
        else:
            # Use pickle for complex objects
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from Redis storage."""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            try:
                return pickle.loads(value)
            except Exception:
                # Return as string if all else fails
                return value.decode('utf-8', errors='ignore')
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set key-value pair with optional expiration and conditions."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_value = self._serialize_value(value)
            result = await self.redis_client.set(
                key, serialized_value, ex=ex, px=px, nx=nx, xx=xx
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error for keys {keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis EXISTS error for keys {keys}: {e}")
            return 0
    
    async def expire(self, key: str, time: int) -> bool:
        """Set expiration time for a key."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get time-to-live for a key."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -1
    
    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment value by amount."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return 0
    
    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement value by amount."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR error for key {key}: {e}")
            return 0
    
    # Hash operations
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash field values."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_mapping = {
                k: self._serialize_value(v) for k, v in mapping.items()
            }
            return await self.redis_client.hset(name, mapping=serialized_mapping)
        except Exception as e:
            logger.error(f"Redis HSET error for hash {name}: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.hget(name, key)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Redis HGET error for hash {name}, key {key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash field values."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            hash_data = await self.redis_client.hgetall(name)
            return {
                k.decode('utf-8'): self._deserialize_value(v)
                for k, v in hash_data.items()
            }
        except Exception as e:
            logger.error(f"Redis HGETALL error for hash {name}: {e}")
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis HDEL error for hash {name}, keys {keys}: {e}")
            return 0
    
    # List operations
    async def lpush(self, name: str, *values: Any) -> int:
        """Push values to the left of a list."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_values = [self._serialize_value(v) for v in values]
            return await self.redis_client.lpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis LPUSH error for list {name}: {e}")
            return 0
    
    async def rpush(self, name: str, *values: Any) -> int:
        """Push values to the right of a list."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_values = [self._serialize_value(v) for v in values]
            return await self.redis_client.rpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis RPUSH error for list {name}: {e}")
            return 0
    
    async def lpop(self, name: str) -> Optional[Any]:
        """Pop value from the left of a list."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.lpop(name)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Redis LPOP error for list {name}: {e}")
            return None
    
    async def rpop(self, name: str) -> Optional[Any]:
        """Pop value from the right of a list."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.rpop(name)
            if value is None:
                return None
            return self._deserialize_value(value)
        except Exception as e:
            logger.error(f"Redis RPOP error for list {name}: {e}")
            return None
    
    async def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """Get list elements in range."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            values = await self.redis_client.lrange(name, start, end)
            return [self._deserialize_value(v) for v in values]
        except Exception as e:
            logger.error(f"Redis LRANGE error for list {name}: {e}")
            return []
    
    async def llen(self, name: str) -> int:
        """Get list length."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.llen(name)
        except Exception as e:
            logger.error(f"Redis LLEN error for list {name}: {e}")
            return 0
    
    # Set operations
    async def sadd(self, name: str, *values: Any) -> int:
        """Add values to a set."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_values = [self._serialize_value(v) for v in values]
            return await self.redis_client.sadd(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis SADD error for set {name}: {e}")
            return 0
    
    async def smembers(self, name: str) -> set:
        """Get all set members."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            members = await self.redis_client.smembers(name)
            return {self._deserialize_value(m) for m in members}
        except Exception as e:
            logger.error(f"Redis SMEMBERS error for set {name}: {e}")
            return set()
    
    async def sismember(self, name: str, value: Any) -> bool:
        """Check if value is a member of set."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            serialized_value = self._serialize_value(value)
            return await self.redis_client.sismember(name, serialized_value)
        except Exception as e:
            logger.error(f"Redis SISMEMBER error for set {name}: {e}")
            return False
    
    # Cache-specific methods
    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set cached value with optional TTL."""
        ttl = ttl or settings.CACHE_TTL_SECONDS
        return await self.set(key, value, ex=ttl)
    
    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value."""
        return await self.get(key)
    
    async def cache_delete(self, pattern: str) -> int:
        """Delete cached values by pattern."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.delete(*[k.decode('utf-8') for k in keys])
            return 0
        except Exception as e:
            logger.error(f"Redis cache delete error for pattern {pattern}: {e}")
            return 0
    
    # Session management
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Create user session."""
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'data': data
        }
        return await self.set(f"session:{session_id}", session_data, ex=ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session."""
        return await self.get(f"session:{session_id}")
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        extend_ttl: bool = True
    ) -> bool:
        """Update user session."""
        session_key = f"session:{session_id}"
        session_data = await self.get(session_key)
        
        if not session_data:
            return False
        
        session_data['data'].update(data)
        session_data['updated_at'] = datetime.utcnow().isoformat()
        
        ttl = await self.ttl(session_key) if extend_ttl else None
        return await self.set(session_key, session_data, ex=ttl)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete user session."""
        return bool(await self.delete(f"session:{session_id}"))
    
    # Queue operations
    async def enqueue(self, queue_name: str, item: Any) -> int:
        """Add item to queue."""
        return await self.rpush(f"queue:{queue_name}", item)
    
    async def dequeue(self, queue_name: str) -> Optional[Any]:
        """Remove item from queue."""
        return await self.lpop(f"queue:{queue_name}")
    
    async def queue_length(self, queue_name: str) -> int:
        """Get queue length."""
        return await self.llen(f"queue:{queue_name}")
    
    # Rate limiting
    async def rate_limit_check(
        self,
        identifier: str,
        limit: int,
        window: int
    ) -> Dict[str, Any]:
        """Check rate limit for identifier."""
        key = f"rate_limit:{identifier}"
        
        try:
            current = await self.incr(key)
            if current == 1:
                await self.expire(key, window)
            
            ttl = await self.ttl(key)
            remaining = max(0, limit - current)
            
            return {
                'allowed': current <= limit,
                'current': current,
                'limit': limit,
                'remaining': remaining,
                'reset_time': ttl,
                'retry_after': ttl if current > limit else 0
            }
        except Exception as e:
            logger.error(f"Rate limit check error for {identifier}: {e}")
            return {
                'allowed': True,
                'current': 0,
                'limit': limit,
                'remaining': limit,
                'reset_time': window,
                'retry_after': 0
            }
    
    # Health and monitoring
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server information."""
        if not self._connected or not self.redis_client:
            return {}
        
        try:
            info = await self.redis_client.info()
            return {
                'redis_version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.error(f"Redis info error: {e}")
            return {}
    
    async def flush_db(self) -> bool:
        """Flush current database (use with caution)."""
        if not self._connected or not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis flush database error: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()