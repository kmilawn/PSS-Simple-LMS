from ninja import Schema, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import validator

# ==================== AUTH SCHEMAS ====================

class RegisterInput(Schema):
    username: str = Field(..., min_length=3, max_length=150)
    email: str = Field(..., min_length=5, max_length=254)
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(
        default="student",
        regex="^(admin|instructor|student)$"
    )

    @validator("email", allow_reuse=True)
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v

class LoginInput(Schema):
    username: str
    password: str

class LoginOutput(Schema):
    access: str
    refresh: str

class RefreshOutput(Schema):
    access: str

class UserOutput(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    bio: Optional[str] = None
    phone: Optional[str] = None
    date_joined: datetime

class UserUpdateInput(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class MessageOutput(Schema):
    message: str

class ErrorOutput(Schema):
    error: str

# ==================== CATEGORY SCHEMAS ====================

class CategoryOutput(Schema):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    children: Optional[List['CategoryOutput']] = None

class CategoryInput(Schema):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None

# ==================== COURSE SCHEMAS ====================

class InstructorOutput(Schema):
    id: int
    username: str
    first_name: str
    last_name: str

class LessonOutput(Schema):
    id: int
    title: str
    content: str
    duration_minutes: int
    order: int
    is_preview: bool

class LessonInput(Schema):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., ge=0, le=300)
    order: int = Field(..., ge=1)
    is_preview: bool = False

class CourseOutput(Schema):
    id: int
    title: str
    slug: str
    description: str
    short_description: Optional[str] = None
    thumbnail: Optional[str] = None
    instructor: InstructorOutput
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    level: str
    price: Decimal
    is_published: bool
    is_featured: bool
    duration_hours: int
    lessons_count: int
    students_enrolled: int
    average_rating: float
    created_at: datetime

class CourseDetailOutput(CourseOutput):
    lessons: List[LessonOutput] = []

class CourseInput(Schema):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    short_description: Optional[str] = None
    category_id: Optional[int] = None
    level: str = Field(default='beginner', regex='^(beginner|intermediate|advanced)$')
    price: Decimal = Field(default=0, ge=0, le=999999)
    is_published: bool = False
    is_featured: bool = False
    duration_hours: int = Field(default=0, ge=0)

class CourseUpdateInput(Schema):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    short_description: Optional[str] = None
    category_id: Optional[int] = None
    level: Optional[str] = Field(None, regex='^(beginner|intermediate|advanced)$')
    price: Optional[Decimal] = Field(None, ge=0, le=999999)
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    duration_hours: Optional[int] = Field(None, ge=0)

# ==================== ENROLLMENT SCHEMAS ====================

class EnrollmentInput(Schema):
    course_id: int

class EnrollmentOutput(Schema):
    id: int
    course_id: int
    course_title: str
    course_thumbnail: Optional[str] = None
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    is_active: bool
    progress_percentage: float
    total_lessons: int
    completed_lessons: int

class ProgressInput(Schema):
    lesson_id: int
    time_spent_seconds: Optional[int] = Field(default=0, ge=0)

class ProgressOutput(Schema):
    lesson_id: int
    lesson_title: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    time_spent_seconds: int

# ==================== PAGINATION ====================

class PaginationInput(Schema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)

class PaginatedResponse(Schema):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int

# Update forward references
CategoryOutput.update_forward_refs()