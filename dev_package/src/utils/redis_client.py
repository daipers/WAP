"""
redis_client.py
===============

Redis client factory with Sentinel support for high availability.
Provides utility methods for distributed state and Pub/Sub coordination.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.sentinel import Sentinel

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client wrapper with Sentinel support.
    """

    _instance: Optional["RedisClient"] = None

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._sentinel: Optional[Sentinel] = None
        self._master_name = os.getenv("REDIS_MASTER_NAME", "mymaster")
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._sentinel_hosts_str = os.getenv("REDIS_SENTINELS", "")

    @classmethod
    def get_instance(cls) -> "RedisClient":
        if cls._instance is None:
            cls._instance = RedisClient()
        return cls._instance

    async def connect(self) -> Redis:
        """Connect to Redis or Sentinel master."""
        if self._redis is not None:
            return self._redis

        if self._sentinel_hosts_str:
            try:
                # Format: host1:port1,host2:port2
                hosts: List[Tuple[str, int]] = []
                for h in self._sentinel_hosts_str.split(","):
                    parts = h.strip().split(":")
                    if len(parts) == 2:
                        hosts.append((parts[0], int(parts[1])))

                self._sentinel = Sentinel(hosts, socket_timeout=0.1)
                self._redis = self._sentinel.master_for(
                    self._master_name, decode_responses=True
                )
                logger.info(f"Connected to Redis Sentinel master: {self._master_name}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis Sentinel: {e}")
                # Fallback to standalone if REDIS_URL is provided
                self._redis = Redis.from_url(self._redis_url, decode_responses=True)
                logger.warning(f"Falling back to standalone Redis: {self._redis_url}")
        else:
            self._redis = Redis.from_url(self._redis_url, decode_responses=True)
            logger.info(f"Connected to standalone Redis: {self._redis_url}")

        return self._redis

    async def get_redis(self) -> Redis:
        """Get the underlying Redis client, connecting if necessary."""
        if self._redis is None:
            await self.connect()
        return self._redis

    async def close(self):
        """Close the Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
        self._sentinel = None

    # Utility methods for session state caching

    async def set_json(self, key: str, value: Any, expire: Optional[int] = None):
        """Store a Python object as JSON in Redis."""
        redis = await self.get_redis()
        json_val = json.dumps(value)
        await redis.set(key, json_val, ex=expire)

    async def get_json(self, key: str) -> Optional[Any]:
        """Retrieve a JSON object from Redis and parse it."""
        redis = await self.get_redis()
        val = await redis.get(key)
        if val:
            return json.loads(val)
        return None

    # Distributed Sets for connection tracking

    async def add_to_set(self, key: str, member: str):
        """Add a member to a Redis set."""
        redis = await self.get_redis()
        await redis.sadd(key, member)

    async def remove_from_set(self, key: str, member: str):
        """Remove a member from a Redis set."""
        redis = await self.get_redis()
        await redis.srem(key, member)

    async def get_set_members(self, key: str) -> List[str]:
        """Get all members of a Redis set."""
        redis = await self.get_redis()
        return list(await redis.smembers(key))

    # Pub/Sub

    async def publish(self, channel: str, message: Any):
        """Publish a message to a channel."""
        redis = await self.get_redis()
        if not isinstance(message, str):
            message = json.dumps(message)
        await redis.publish(channel, message)

    async def subscribe(self, *channels: str):
        """Return a PubSub object subscribed to channels."""
        redis = await self.get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    # Distributed Locking

    async def acquire_lock(self, lock_name: str, timeout: int = 10) -> bool:
        """Acquire a simple distributed lock."""
        redis = await self.get_redis()
        # NX=True means only set if it doesn't exist
        return await redis.set(f"lock:{lock_name}", "1", ex=timeout, nx=True)

    async def release_lock(self, lock_name: str):
        """Release a distributed lock."""
        redis = await self.get_redis()
        await redis.delete(f"lock:{lock_name}")
