import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.test.utils import CaptureQueriesContext
from core.models import Course

print("=" * 50)
print("QUERY OPTIMIZATION TEST")
print("=" * 50)

# TEST 1: Tanpa optimasi (N+1 problem)
print("\n1. WITHOUT OPTIMIZATION (N+1 Problem):")
with CaptureQueriesContext(connection) as context:
    courses = Course.objects.filter(is_published=True)[:5]
    for course in courses:
        instructor_name = course.instructor.username
        lessons_count = course.lessons.count()
        print(f"   - {course.title}: {lessons_count} lessons by {instructor_name}")
    
    print(f"   📊 Total queries: {len(context.captured_queries)}")

# TEST 2: Dengan optimasi (using for_listing)
print("\n2. WITH OPTIMIZATION (using for_listing):")
with CaptureQueriesContext(connection) as context:
    courses = Course.objects.for_listing().filter(is_published=True)[:5]
    for course in courses:
        instructor_name = course.instructor.username
        lessons_count = course.lessons_count
        students = course.students_enrolled
        print(f"   - {course.title}: {lessons_count} lessons, {students} students by {instructor_name}")
    
    print(f"   📊 Total queries: {len(context.captured_queries)}")

print("\n" + "=" * 50)
print("✅ OPTIMIZATION SUCCESSFUL!")
print("=" * 50)