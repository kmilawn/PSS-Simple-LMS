import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Enrollment, Progress
from django.db.models import Count, Q

print("=" * 50)
print("STUDENT PROGRESS")
print("=" * 50)

enrollments = Enrollment.objects.annotate(
    total_lessons=Count('course__lessons'),
    completed_lessons=Count('progress', filter=Q(progress__is_completed=True))
).filter(total_lessons__gt=0)

for e in enrollments:
    progress = (e.completed_lessons / e.total_lessons * 100) if e.total_lessons > 0 else 0
    if progress >= 100:
        print(f'✅ {e.student.username} -> {e.course.title}: {progress:.0f}% (COMPLETED)')
    else:
        print(f'   {e.student.username} -> {e.course.title}: {progress:.0f}%')

print("=" * 50)
print(f"Total enrollments with lessons: {enrollments.count()}")