from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Category, Course, Lesson, Enrollment, Progress, Review
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate sample data for testing'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n📚 GENERATING SAMPLE DATA...\n'))
        
        # 1. Create Categories
        self.stdout.write('Creating categories...')
        categories = {
            'programming': Category.objects.create(name='Programming', slug='programming'),
            'web-dev': Category.objects.create(name='Web Development', slug='web-dev', parent=Category.objects.get(slug='programming')),
            'data-science': Category.objects.create(name='Data Science', slug='data-science', parent=Category.objects.get(slug='programming')),
            'mobile-dev': Category.objects.create(name='Mobile Development', slug='mobile-dev', parent=Category.objects.get(slug='programming')),
        }
        self.stdout.write(f'  ✅ Created {len(categories)} categories')
        
        # 2. Create Users
        self.stdout.write('\nCreating users...')
        
        # Admin
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@lms.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin.set_password('admin123')
        admin.save()
        
        # Instructors
        instructors = []
        for i in range(3):
            instructor, _ = User.objects.get_or_create(
                username=f'instructor{i+1}',
                defaults={
                    'email': f'instructor{i+1}@lms.com',
                    'role': 'instructor',
                    'first_name': f'Instructor{i+1}',
                    'last_name': 'User'
                }
            )
            instructor.set_password('password123')
            instructor.save()
            instructors.append(instructor)
        
        # Students
        students = []
        for i in range(5):
            student, _ = User.objects.get_or_create(
                username=f'student{i+1}',
                defaults={
                    'email': f'student{i+1}@example.com',
                    'role': 'student',
                    'first_name': f'Student{i+1}',
                    'last_name': 'User'
                }
            )
            student.set_password('password123')
            student.save()
            students.append(student)
        
        self.stdout.write(f'  ✅ Created 1 admin, {len(instructors)} instructors, {len(students)} students')
        
        # 3. Create Courses
        self.stdout.write('\nCreating courses...')
        
        course_data = [
            {'title': 'Python Programming Fundamentals', 'level': 'beginner', 'duration': 20},
            {'title': 'Advanced Django Development', 'level': 'advanced', 'duration': 30},
            {'title': 'React.js Complete Guide', 'level': 'intermediate', 'duration': 25},
            {'title': 'Data Analysis with Pandas', 'level': 'intermediate', 'duration': 15},
            {'title': 'Machine Learning Basics', 'level': 'advanced', 'duration': 35},
            {'title': 'Flutter Mobile Development', 'level': 'beginner', 'duration': 28},
        ]
        
        courses = []
        for data in course_data:
            course = Course.objects.create(
                title=data['title'],
                slug=data['title'].lower().replace(' ', '-'),
                description=f'Complete course on {data["title"]}',
                short_description=f'Learn {data["title"]} from scratch',
                instructor=random.choice(instructors),
                category=random.choice(list(categories.values())),
                level=data['level'],
                price=Decimal(random.randint(0, 99)),
                is_published=True,
                is_featured=random.choice([True, False]),
                duration_hours=data['duration']
            )
            courses.append(course)
        
        self.stdout.write(f'  ✅ Created {len(courses)} courses')
        
        # 4. Create Lessons
        self.stdout.write('\nCreating lessons...')
        lessons_count = 0
        
        for course in courses:
            lesson_titles = [
                f'Introduction to {course.title}',
                'Core Concepts',
                'Advanced Topics',
                'Practical Examples',
                'Project Work',
                'Final Assessment'
            ]
            for i, title in enumerate(lesson_titles[:random.randint(4, 6)], 1):
                Lesson.objects.create(
                    course=course,
                    title=title,
                    content=f'This is the content for {title}',
                    duration_minutes=random.randint(10, 45),
                    order=i,
                    is_published=True
                )
                lessons_count += 1
        
        self.stdout.write(f'  ✅ Created {lessons_count} lessons')
        
        # 5. Create Enrollments and Progress
        self.stdout.write('\nCreating enrollments and progress...')
        enrollments_count = 0
        
        for student in students:
            for course in random.sample(courses, random.randint(2, 4)):
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    is_active=True
                )
                enrollments_count += 1
                
                # Create progress for lessons
                lessons = list(course.lessons.all())
                completed_count = random.randint(0, len(lessons))
                
                for i, lesson in enumerate(lessons[:completed_count]):
                    Progress.objects.create(
                        enrollment=enrollment,
                        lesson=lesson,
                        is_completed=True,
                        completed_at=None,
                        time_spent_seconds=random.randint(300, 3600)
                    )
                
                # Mark course as completed if all lessons done
                if completed_count == len(lessons):
                    enrollment.complete()
        
        self.stdout.write(f'  ✅ Created {enrollments_count} enrollments')
        
        # 6. Create Reviews
        self.stdout.write('\nCreating reviews...')
        reviews_count = 0
        
        for student in students:
            for enrollment in student.enrollments.all():
                if random.random() > 0.5:
                    Review.objects.create(
                        course=enrollment.course,
                        student=student,
                        rating=random.randint(3, 5),
                        comment=f'Great course! Really enjoyed learning {enrollment.course.title}.'
                    )
                    reviews_count += 1
        
        self.stdout.write(f'  ✅ Created {reviews_count} reviews')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('✅ SAMPLE DATA GENERATED SUCCESSFULLY!'))
        self.stdout.write('='*50)
        self.stdout.write(f'\n📊 Statistics:')
        self.stdout.write(f'  • Categories: {Category.objects.count()}')
        self.stdout.write(f'  • Users: {User.objects.count()}')
        self.stdout.write(f'  • Courses: {Course.objects.count()}')
        self.stdout.write(f'  • Lessons: {Lesson.objects.count()}')
        self.stdout.write(f'  • Enrollments: {Enrollment.objects.count()}')
        self.stdout.write(f'  • Progress: {Progress.objects.count()}')
        self.stdout.write(f'  • Reviews: {Review.objects.count()}')
        self.stdout.write('\n🔐 Default Passwords:')
        self.stdout.write('  • Admin: admin / admin123')
        self.stdout.write('  • Instructors: instructor1,2,3 / password123')
        self.stdout.write('  • Students: student1,2,3,4,5 / password123')
        self.stdout.write('\n🌐 Access admin panel at: http://localhost:8000/admin\n')