from ninja.security import HttpBearer
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
import jwt
from django.conf import settings

User = get_user_model()

class JWTAuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            # Decode token
            decoded = AccessToken(token)
            user_id = decoded.get('user_id')
            
            if user_id:
                user = User.objects.get(id=user_id)
                request.user = user
                return token
            
            return None
            
        except Exception as e:
            return None

# Instance untuk digunakan di API
jwt_auth = JWTAuthBearer()

# Decorators untuk role-based access
def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

def is_instructor(user):
    return user.is_authenticated and (user.role == 'instructor' or user.role == 'admin')

def is_student(user):
    return user.is_authenticated and (user.role == 'student' or user.role == 'admin')

def is_owner_or_admin(course, user):
    """Check if user is course owner or admin"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin' or user.is_superuser:
        return True
    return course.instructor_id == user.id