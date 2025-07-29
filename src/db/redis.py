import redis.asyncio as aioredis
from src.config import Config

# It's good practice to name constants with their units for clarity.
JTI_EXPIRY_SECONDS = 3600

# Create a global Redis client instance.
# decode_responses=True ensures that we get strings back from Redis, not bytes.
token_blocklist = aioredis.from_url(
    Config.REDIS_URL,
    decode_responses=True
)


async def add_jti_to_blocklist(jti:str) -> None:
    """Adds a JWT's JTI to the Redis blocklist with an expiry."""
    # The correct method is `set()`. The client instance itself is not callable.
    await token_blocklist.set(name=jti, value="", ex=JTI_EXPIRY_SECONDS)

async def token_in_blocklist(jti:str) -> bool:
    """Checks if a JTI exists in the Redis blocklist."""
    # Use a different variable name for the result to avoid shadowing the input `jti`.
    result = await token_blocklist.get(jti)
    return result is not None
