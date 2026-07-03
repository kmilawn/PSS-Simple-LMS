from django.http import JsonResponse
from django.core.cache import cache
import re

# List of paths to exclude from rate limiting
EXEMPT_PATHS = [
    r'^/api/docs',
    r'^/api/openapi.json',
    r'^/admin/',
]

class RateLimitMiddleware:
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for exempt paths
        path = request.path
        for exempt_pattern in EXEMPT_PATHS:
            if re.match(exempt_pattern, path):
                return self.get_response(request)
        
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Create cache key
        key = f"rate_limit:{ip}"
        
        # Get current request count
        count = cache.get(key, 0)
        
        # Rate limit: 60 requests per minute
        if count >= 60:
            return JsonResponse(
                {"error": "Rate limit exceeded. Please try again later."},
                status=429
            )
        
        # Increment counter
        cache.set(key, count + 1, timeout=60)
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip