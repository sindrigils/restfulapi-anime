import redis
from datetime import timedelta
from json import loads, dumps
from typing import Any

rd = redis.Redis(host="localhost", port=6379, db=0)
CACHE_EXPIRE_TIME = timedelta(minutes=5).seconds


def get_cache(key: str) -> Any:
    key = rd.get(key)
    if key:
        key_decoded = key.decode("utf-8")
        return loads(key_decoded)
    return None


def insert_cache(key: str, value: str):
    json_value = dumps(value)
    encoded_value = json_value.encode("utf-8")
    rd.setex(key, CACHE_EXPIRE_TIME, encoded_value)
