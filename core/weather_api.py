import json
import time
import redis

redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

def get_weather(city):
    """
    Simulasi API Call dengan Redis Cache
    """

    cache_key = f"weather:{city}"

    # CEK CACHE DULU
    cached_data = redis_client.get(cache_key)

    if cached_data:

        print("CACHE HIT")

        return json.loads(cached_data)

    print("CACHE MISS")

    # Simulasi API lambat
    time.sleep(2)

    result = {
        "city": city,
        "temperature": 30,
        "condition": "Sunny"
    }

    # SIMPAN KE CACHE 5 MENIT
    redis_client.setex(
        cache_key,
        300,
        json.dumps(result)
    )

    return result