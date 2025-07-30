"""
Redis connection and JWT blocklist management.
"""

import redis.asyncio as redis
from typing import Optional
from src.config import Config
import logging

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for JWT token blocklist management."""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection with production-ready configuration."""
        try:
            connection_params = {
                "encoding": "utf-8",
                "decode_responses": True,
                "socket_connect_timeout": 5,  # 5 second connection timeout
                "socket_timeout": 5,          # 5 second socket timeout
                "retry_on_timeout": True,     # Retry on timeout
                "health_check_interval": 30   # Health check every 30 seconds
            }

            if Config.REDIS_URL:
                self.redis = redis.from_url(Config.REDIS_URL, **connection_params)
            else:
                self.redis = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                    **connection_params
                )

            # Test connection
            await self.redis.ping()
            logger.info(f"Redis connection established successfully to {Config.REDIS_HOST}:{Config.REDIS_PORT}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def is_connected(self) -> bool:
        """Check if Redis is connected."""
        if not self.redis:
            return False
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def add_to_blocklist(self, jti: str, expires_in: int):
        """
        Add a JWT token ID to the blocklist.
        
        Args:
            jti: JWT token ID
            expires_in: Time in seconds until token expires
        """
        if not self.redis:
            logger.warning("Redis not connected, cannot add token to blocklist")
            return False
        
        try:
            # Use the JTI as key and set expiration to match token expiration
            await self.redis.setex(f"blocklist:{jti}", expires_in, "1")
            logger.info(f"Token {jti} added to blocklist")
            return True
        except Exception as e:
            logger.error(f"Failed to add token to blocklist: {e}")
            return False
    
    async def is_token_blocked(self, jti: str) -> bool:
        """
        Check if a JWT token ID is in the blocklist.
        
        Args:
            jti: JWT token ID
            
        Returns:
            True if token is blocked, False otherwise
        """
        if not self.redis:
            logger.warning("Redis not connected, assuming token is not blocked")
            return False
        
        try:
            result = await self.redis.exists(f"blocklist:{jti}")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to check token blocklist: {e}")
            return False
    
    async def remove_from_blocklist(self, jti: str):
        """
        Remove a JWT token ID from the blocklist.
        
        Args:
            jti: JWT token ID
        """
        if not self.redis:
            logger.warning("Redis not connected, cannot remove token from blocklist")
            return False
        
        try:
            result = await self.redis.delete(f"blocklist:{jti}")
            logger.info(f"Token {jti} removed from blocklist")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to remove token from blocklist: {e}")
            return False
    
    async def get_blocklist_size(self) -> int:
        """Get the number of blocked tokens."""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys("blocklist:*")
            return len(keys)
        except Exception as e:
            logger.error(f"Failed to get blocklist size: {e}")
            return 0
    
    async def clear_blocklist(self):
        """Clear all blocked tokens (for testing purposes)."""
        if not self.redis:
            return False

        try:
            keys = await self.redis.keys("blocklist:*")
            if keys:
                await self.redis.delete(*keys)
            logger.info("Blocklist cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear blocklist: {e}")
            return False

    async def get_redis_info(self) -> dict:
        """Get Redis server information for monitoring."""
        if not self.redis:
            return {"status": "disconnected"}

        try:
            info = await self.redis.info()
            return {
                "status": "connected",
                "version": info.get("redis_version"),
                "memory_used": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"status": "error", "error": str(e)}

    async def health_check(self) -> bool:
        """Perform Redis health check."""
        try:
            if not self.redis:
                return False

            # Test basic operations
            test_key = "health_check_test"
            await self.redis.setex(test_key, 1, "test")
            result = await self.redis.get(test_key)
            await self.redis.delete(test_key)

            return result == "test"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()


async def get_redis_service() -> RedisService:
    """Dependency to get Redis service instance."""
    return redis_service


async def startup_redis():
    """Initialize Redis connection on app startup."""
    await redis_service.connect()


async def shutdown_redis():
    """Close Redis connection on app shutdown."""
    await redis_service.disconnect()
