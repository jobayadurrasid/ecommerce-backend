from redis import Redis
from app.core.config import settings
from app.core.logger import logger


class RedisClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._client = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {e}")
                cls._client = None
        return cls._instance

    @property
    def client(self) -> Redis | None:
        if self._client is None:
            try:
                self._client = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
            except Exception as e:
                logger.warning(f"Redis is currently unavailable: {e}")
                return None
        return self._client


redis_client = RedisClient()
