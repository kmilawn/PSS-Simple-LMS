from ninja import NinjaAPI
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q
from typing import List, Optional
from datetime import datetime
from django.core.cache import cache
from django.utils.text import slugify

from . import schemas
from .models import User, Category, Course, Lesson, Enrollment, Progress
from .tasks import send_enrollment_email, generate_certificate

User = get_user_model()

# Create API instance
api = NinjaAPI(
    title="Simple LMS API",
    version="1.0.0",
    description="Learning Management System API with JWT Authentication",
    docs_url="/docs",
    urls_namespace="api"
)

# Authentication
jwt_auth = JWTAuth()

# ==================== HELPER FUNCTIONS ====================

def get_real_user(user):
    """Get actual User object from request.user"""
    try:
        if hasattr(user, 'id') and user.id:
            return User.objects.get(id=user.id)
        return None
    except (User.DoesNotExist, AttributeError):
        return None

def is_admin(user):
    """Check if user is admin"""
    if not user or not user.is_authenticated:
        return False
    real_user = get_real_user(user)
    if not real_user:
        return False
    return real_user.role == "admin" or real_user.is_superuser

def is_instructor(user):
    """Check if user is instructor or admin"""
    if not user or not user.is_authenticated:
        return False
    real_user = get_real_user(user)
    if not real_user:
        return False
    return real_user.role == "instructor" or real_user.role == "admin"

def is_student(user):
    """Check if user is student"""
    if not user or not user.is_authenticated:
        return False
    real_user = get_real_user(user)
    if not real_user:
        return False
    return real_user.role == "student"

def is_owner_or_admin(course, user):
    """Check if user is course owner or admin"""
    if not user or not user.is_authenticated:
        return False
    real_user = get_real_user(user)
    if not real_user:
        return False
    if real_user.role == "admin" or real_user.is_superuser:
        return True
    return course.instructor_id == real_user.id

# ==================== AUTH ENDPOINTS ====================

@api.post("/auth/register", response={201: schemas.UserOutput, 400: schemas.ErrorOutput})
def register(request, payload: schemas.RegisterInput):
    """Register new user"""
    
    if User.objects.filter(username=payload.username).exists():
        return 400, {"error": "Username already exists"}
    
    if User.objects.filter(email=payload.email).exists():
        return 400, {"error": "Email already exists"}
    
    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name or '',
        last_name=payload.last_name or '',
        role=payload.role
    )
    
    return 201, schemas.UserOutput(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        bio=user.bio or '',
        phone=user.phone or '',
        date_joined=user.date_joined
    )

@api.post("/auth/login", response={200: dict, 401: schemas.ErrorOutput})
def login(request, payload: schemas.LoginInput):
    """Login and get JWT tokens"""
    
    user = authenticate(username=payload.username, password=payload.password)
    
    if user is None:
        return 401, {"error": "Invalid credentials"}
    
    refresh = RefreshToken.for_user(user)
    
    return 200, {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

@api.post("/auth/refresh", response={200: dict, 401: schemas.ErrorOutput})
def refresh_token(request, payload: schemas.RefreshInput):
    """Refresh access token"""
    
    if not payload.refresh:
        return 401, {"error": "Refresh token required"}
    
    try:
        refresh = RefreshToken(payload.refresh)
        return 200, {"access": str(refresh.access_token)}
    except Exception:
        return 401, {"error": "Invalid refresh token"}

@api.get("/auth/me", auth=jwt_auth, response={200: schemas.UserOutput, 401: schemas.ErrorOutput})
def get_me(request):
    """Get current user info"""
    try:
        user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        return 401, {"error": "User not found"}
    
    return 200, schemas.UserOutput(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        bio=user.bio or '',
        phone=user.phone or '',
        date_joined=user.date_joined
    )

@api.put("/auth/me", auth=jwt_auth, response={200: schemas.UserOutput, 401: schemas.ErrorOutput})
def update_me(request, payload: schemas.UserUpdateInput):
    """Update current user profile"""
    try:
        user = User.objects.get(id=request.user.id)
    except User.DoesNotExist:
        return 401, {"error": "User not found"}
    
    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.bio is not None:
        user.bio = payload.bio
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.email is not None:
        user.email = payload.email
    
    user.save()
    
    return 200, schemas.UserOutput(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        bio=user.bio or '',
        phone=user.phone or '',
        date_joined=user.date_joined
    )

# ==================== COURSES ENDPOINTS ====================

@api.get("/courses", response=List[schemas.CourseOutput])
def list_courses(
    request,
    category_id: Optional[int] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None
):
    """List all published courses with filters"""
    
    # Build cache key
    cache_key = f"course_list_{category_id}_{level}_{search}_{featured}"
    
    print(f"🔍 Cache key: {cache_key}")

    cached_data = cache.get(cache_key)
    
    if cached_data:
        print(f"✅ Cache HIT for {cache_key}")
        return cached_data
    else:
        print(f"❌ Cache MISS for {cache_key}")
    
    courses = Course.objects.filter(is_published=True).select_related('category', 'instructor')
    
    if category_id:
        courses = courses.filter(category_id=category_id)
    
    if level:
        courses = courses.filter(level=level)
    
    if featured:
        courses = courses.filter(is_featured=True)
    
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    result = []
    for course in courses[:50]:
        result.append(schemas.CourseOutput(
            id=course.id,
            title=course.title,
            slug=course.slug,
            description=course.description,
            short_description=course.short_description or '',
            thumbnail=course.thumbnail.url if course.thumbnail else None,
            instructor=schemas.InstructorOutput(
                id=course.instructor.id,
                username=course.instructor.username,
                first_name=course.instructor.first_name,
                last_name=course.instructor.last_name
            ),
            category_id=course.category.id if course.category else None,
            category_name=course.category.name if course.category else None,
            level=course.level,
            price=course.price,
            is_published=course.is_published,
            is_featured=course.is_featured,
            duration_hours=course.duration_hours,
            lessons_count=course.lessons.count(),
            students_enrolled=course.enrollments.filter(is_active=True).count(),
            average_rating=course.reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            created_at=course.created_at
        ))
    
    print(f"💾 Saving to cache: {cache_key}")
    cache.set(cache_key, result, timeout=300)
    
    return result

@api.get("/courses/{course_id}", response=schemas.CourseDetailOutput)
def get_course(request, course_id: int):
    """Get course detail with lessons"""
    
    cache_key = f"course_{course_id}"
    cached = cache.get(cache_key)
    
    if cached:
        return cached
    
    course = get_object_or_404(
        Course.objects.select_related('category', 'instructor'), 
        id=course_id, 
        is_published=True
    )
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            student=request.user, 
            course=course, 
            is_active=True
        ).exists()
    
    # Filter lessons based on enrollment
    lessons = course.lessons.all()
    if not request.user.is_authenticated:
        lessons = lessons.filter(is_preview=True)
    elif request.user.is_authenticated and not is_enrolled:
        user = User.objects.get(id=request.user.id)
        if user.role != 'instructor':
            lessons = lessons.filter(is_preview=True)
    
    response = schemas.CourseDetailOutput(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        short_description=course.short_description or '',
        thumbnail=course.thumbnail.url if course.thumbnail else None,
        instructor=schemas.InstructorOutput(
            id=course.instructor.id,
            username=course.instructor.username,
            first_name=course.instructor.first_name,
            last_name=course.instructor.last_name
        ),
        category_id=course.category.id if course.category else None,
        category_name=course.category.name if course.category else None,
        level=course.level,
        price=course.price,
        is_published=course.is_published,
        is_featured=course.is_featured,
        duration_hours=course.duration_hours,
        lessons_count=course.lessons.count(),
        students_enrolled=course.enrollments.filter(is_active=True).count(),
        average_rating=course.reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        created_at=course.created_at,
        lessons=[
            schemas.LessonOutput(
                id=l.id,
                title=l.title,
                content=l.content,
                duration_minutes=l.duration_minutes,
                order=l.order,
                is_preview=l.is_preview
            ) for l in lessons
        ]
    )
    
    cache.set(cache_key, response, timeout=300)
    
    return response

@api.post("/courses", auth=jwt_auth, response={201: schemas.CourseOutput, 401: schemas.ErrorOutput, 403: schemas.ErrorOutput})
def create_course(request, payload: schemas.CourseInput):
    """Create new course (Instructor/Admin only)"""
    
    if not request.user.is_authenticated:
        return 401, {"error": "Not authenticated"}
    
    real_user = User.objects.get(id=request.user.id)
    
    if not is_instructor(real_user):
        return 403, {"error": "Only instructors can create courses"}
    
    category = None
    if payload.category_id:
        category = get_object_or_404(Category, id=payload.category_id)
    
    course = Course.objects.create(
        title=payload.title,
        slug=slugify(payload.title),
        description=payload.description,
        short_description=payload.short_description or '',
        instructor=real_user,
        category=category,
        level=payload.level,
        price=payload.price,
        is_published=payload.is_published,
        is_featured=payload.is_featured,
        duration_hours=payload.duration_hours
    )
    
    # Clear cache
    cache.clear()
    
    return 201, schemas.CourseOutput(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        short_description=course.short_description,
        thumbnail=None,
        instructor=schemas.InstructorOutput(
            id=course.instructor.id,
            username=course.instructor.username,
            first_name=course.instructor.first_name,
            last_name=course.instructor.last_name
        ),
        category_id=course.category.id if course.category else None,
        category_name=course.category.name if course.category else None,
        level=course.level,
        price=course.price,
        is_published=course.is_published,
        is_featured=course.is_featured,
        duration_hours=course.duration_hours,
        lessons_count=0,
        students_enrolled=0,
        average_rating=0,
        created_at=course.created_at
    )

@api.patch("/courses/{course_id}", auth=jwt_auth, response={200: schemas.CourseOutput, 401: schemas.ErrorOutput, 403: schemas.ErrorOutput})
def update_course(request, course_id: int, payload: schemas.CourseUpdateInput):
    """Update course (Owner only)"""
    
    if not request.user.is_authenticated:
        return 401, {"error": "Not authenticated"}
    
    course = get_object_or_404(Course, id=course_id)
    real_user = User.objects.get(id=request.user.id)
    
    if not is_owner_or_admin(course, real_user):
        return 403, {"error": "You don't have permission to edit this course"}
    
    if payload.title is not None:
        course.title = payload.title
        course.slug = slugify(payload.title)
    if payload.description is not None:
        course.description = payload.description
    if payload.short_description is not None:
        course.short_description = payload.short_description
    if payload.category_id is not None:
        course.category = get_object_or_404(Category, id=payload.category_id)
    if payload.level is not None:
        course.level = payload.level
    if payload.price is not None:
        course.price = payload.price
    if payload.is_published is not None:
        course.is_published = payload.is_published
    if payload.is_featured is not None:
        course.is_featured = payload.is_featured
    if payload.duration_hours is not None:
        course.duration_hours = payload.duration_hours
    
    course.save()
    
    # Clear cache
    cache.clear()
    
    return 200, schemas.CourseOutput(
        id=course.id,
        title=course.title,
        slug=course.slug,
        description=course.description,
        short_description=course.short_description or '',
        thumbnail=course.thumbnail.url if course.thumbnail else None,
        instructor=schemas.InstructorOutput(
            id=course.instructor.id,
            username=course.instructor.username,
            first_name=course.instructor.first_name,
            last_name=course.instructor.last_name
        ),
        category_id=course.category.id if course.category else None,
        category_name=course.category.name if course.category else None,
        level=course.level,
        price=course.price,
        is_published=course.is_published,
        is_featured=course.is_featured,
        duration_hours=course.duration_hours,
        lessons_count=course.lessons.count(),
        students_enrolled=course.enrollments.filter(is_active=True).count(),
        average_rating=course.reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
        created_at=course.created_at
    )

@api.delete("/courses/{course_id}", auth=jwt_auth, response={200: schemas.MessageOutput, 401: schemas.ErrorOutput, 403: schemas.ErrorOutput})
def delete_course(request, course_id: int):
    """Delete course (Admin only)"""
    
    if not request.user.is_authenticated:
        return 401, {"error": "Not authenticated"}
    
    real_user = User.objects.get(id=request.user.id)
    
    if not is_admin(real_user):
        return 403, {"error": "Only admin can delete courses"}
    
    course = get_object_or_404(Course, id=course_id)
    
    # Clear cache
    cache.clear()
    
    course.delete()
    
    return 200, {"message": "Course deleted successfully"}

# ==================== ENROLLMENTS ENDPOINTS ====================

@api.post("/enrollments", auth=jwt_auth, response={201: schemas.EnrollmentOutput, 400: schemas.ErrorOutput, 401: schemas.ErrorOutput, 403: schemas.ErrorOutput})
def enroll_course(request, payload: schemas.EnrollmentInput):
    """Enroll to a course (Student only)"""
    
    if not request.user.is_authenticated:
        return 401, {"error": "Not authenticated"}
    
    real_user = User.objects.get(id=request.user.id)
    
    if not is_student(real_user):
        return 403, {"error": "Only students can enroll to courses"}
    
    course = get_object_or_404(Course, id=payload.course_id, is_published=True)
    
    if Enrollment.objects.filter(student=real_user, course=course).exists():
        return 400, {"error": "Already enrolled in this course"}
    
    enrollment = Enrollment.objects.create(
        student=real_user,
        course=course,
        is_active=True
    )

    # Trigger email async
    send_enrollment_email.delay(real_user.username, course.title)
    
    total_lessons = course.lessons.count()
    
    return 201, schemas.EnrollmentOutput(
        id=enrollment.id,
        course_id=course.id,
        course_title=course.title,
        course_thumbnail=course.thumbnail.url if course.thumbnail else None,
        enrolled_at=enrollment.enrolled_at,
        completed_at=enrollment.completed_at,
        is_active=enrollment.is_active,
        progress_percentage=0,
        total_lessons=total_lessons,
        completed_lessons=0
    )

@api.get("/enrollments/my-courses", auth=jwt_auth, response=List[schemas.EnrollmentOutput])
def my_courses(request):
    """Get current user's enrolled courses with progress"""
    
    if not request.user.is_authenticated:
        return []
    
    real_user = User.objects.get(id=request.user.id)
    
    enrollments = Enrollment.objects.filter(student=real_user, is_active=True).select_related('course', 'course__instructor')
    
    result = []
    for enrollment in enrollments:
        total_lessons = enrollment.course.lessons.count()
        completed_lessons = enrollment.progress.filter(is_completed=True).count()
        progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        result.append(schemas.EnrollmentOutput(
            id=enrollment.id,
            course_id=enrollment.course.id,
            course_title=enrollment.course.title,
            course_thumbnail=enrollment.course.thumbnail.url if enrollment.course.thumbnail else None,
            enrolled_at=enrollment.enrolled_at,
            completed_at=enrollment.completed_at,
            is_active=enrollment.is_active,
            progress_percentage=progress,
            total_lessons=total_lessons,
            completed_lessons=completed_lessons
        ))
    
    return result

@api.post("/enrollments/{enrollment_id}/progress", auth=jwt_auth, response={200: schemas.ProgressOutput, 401: schemas.ErrorOutput, 404: schemas.ErrorOutput})
def mark_lesson_complete(request, enrollment_id: int, payload: schemas.ProgressInput):
    """Mark a lesson as complete for an enrollment"""
    
    if not request.user.is_authenticated:
        return 401, {"error": "Not authenticated"}
    
    real_user = User.objects.get(id=request.user.id)
    
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=real_user)
    lesson = get_object_or_404(Lesson, id=payload.lesson_id, course=enrollment.course)
    
    progress, created = Progress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = datetime.now()
        progress.time_spent_seconds = payload.time_spent_seconds or 0
        progress.save()
        
        # Check if course is completed
        total_lessons = enrollment.course.lessons.count()
        completed_lessons = enrollment.progress.filter(is_completed=True).count()
        
        if completed_lessons == total_lessons:
            enrollment.complete()
            from .tasks import generate_certificate
            generate_certificate.delay(real_user.username, enrollment.course.title)
    
    return 200, schemas.ProgressOutput(
        lesson_id=lesson.id,
        lesson_title=lesson.title,
        is_completed=progress.is_completed,
        completed_at=progress.completed_at,
        time_spent_seconds=progress.time_spent_seconds
    )

# ==================== CATEGORY ENDPOINTS ====================

@api.get("/categories", response=List[schemas.CategoryOutput])
def list_categories(request):
    """List all categories"""
    categories = Category.objects.filter(parent__isnull=True)
    
    result = []
    for cat in categories:
        children = Category.objects.filter(parent=cat)
        result.append(schemas.CategoryOutput(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description or '',
            parent_id=None,
            parent_name=None,
            children=[
                schemas.CategoryOutput(
                    id=c.id,
                    name=c.name,
                    slug=c.slug,
                    description=c.description or '',
                    parent_id=cat.id,
                    parent_name=cat.name,
                    children=[]
                ) for c in children
            ]
        ))
    
    return result