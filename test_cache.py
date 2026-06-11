import time

from core.weather_api import get_weather

print("Testing Redis Cache")

# First Call
start = time.time()

result1 = get_weather("Jakarta")

time1 = time.time() - start

print("Result:", result1)
print(f"First Call: {time1:.2f}s")


# Second Call
start = time.time()

result2 = get_weather("Jakarta")

time2 = time.time() - start

print("Result:", result2)
print(f"Second Call (Cached): {time2:.2f}s")