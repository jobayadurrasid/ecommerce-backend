from redis import Redis
from app.core.config import settings


class RedisClient:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return cls._instance

    @property
    def client(self) -> Redis:
        return self._client