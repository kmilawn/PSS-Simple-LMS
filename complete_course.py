import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Course, Enrollment, Lesson, Progress

User = get_user_model()

print("=" * 50)
print("COMPLETE COURSE FOR CERTIFICATE TEST")
print("=" * 50)

# Cari student
student = User.objects.filter(username='cert_test').first()
if not student:
    student = User.objects.create_user(
        username='cert_test',
        email='cert@test.com',
        password='test123',
        role='student'
    )
    print(f'✅ Student created: cert_test / test123')
else:
    print(f'✅ Student found: {student.username}')

# Cari course yang punya lesson
course = Course.objects.filter(lessons__isnull=False).first()
if not course:
    print('❌ No course with lessons found!')
    print('Please create a course with lessons first.')
    exit()

print(f'📚 Course: {course.title} (ID: {course.id})')

# Enroll
enrollment, created = Enrollment.objects.get_or_create(
    student=student,
    course=course,
    defaults={'is_active': True}
)
if created:
    print(f'📝 New enrollment created: {enrollment.id}')
else:
    print(f'📝 Existing enrollment: {enrollment.id}')

# Complete semua lesson
lessons = course.lessons.all()
completed = 0
skipped = 0

for lesson in lessons:
    progress, created = Progress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = datetime.now()
        progress.time_spent_seconds = 300
        progress.save()
        completed += 1
    else:
        skipped += 1

# Mark course as completed
enrollment.complete()
print(f'✅ Completed {completed} new lessons, {skipped} already completed')
print(f'✅ Course marked as completed!')

if completed > 0:
    print('\n🎯 Certificate task should be triggered!')
    print('\n📌 Check celery worker log:')
    print('   docker-compose logs celery-worker --tail=30 | findstr certificate')
    print('\n📌 Check MongoDB:')
    print('   docker-compose exec mongodb mongosh --eval "use simple_lms; db.activity_logs.find({task: \"generate_certificate\"}).pretty()"')
else:
    print('\n⚠️ No new lessons were completed. Certificate might already be generated.')