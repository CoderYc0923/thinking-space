from functools import lru_cache

import redis

from core.config import settings

# lru_cache 缓存最近使用的元素，超限删除最久未使用的元素
@lru_cache
def get_redis() -> redis.Redis:
    """
    进程内复用连接池。
    decode_responses=True 将返回值转换为字符串。
    """

    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )

def stock_key(product_id: int) -> str:
    return f"seckill:stock:{product_id}"

def bought_key(product_id: int) -> str:
    return f"seckill:bought:{product_id}"
