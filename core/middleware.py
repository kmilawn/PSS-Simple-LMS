from django.http import JsonResponse
from django.core.cache import cache


class RateLimitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        ip = request.META.get(
            "REMOTE_ADDR"
        )

        key = f"rate:{ip}"

        count = cache.get(
            key,
            0
        )

        if count >= 60:

            return JsonResponse(
                {
                    "error":
                    "Rate limit exceeded"
                },
                status=429
            )

        cache.set(
            key,
            count + 1,
            timeout=60
        )

        return self.get_response(
            request
        )