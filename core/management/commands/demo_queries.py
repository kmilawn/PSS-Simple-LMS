from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.contrib.auth import get_user_model
from core.models import Course, Enrollment
import time

User = get_user_model()

class Command(BaseCommand):
    help = 'Demo query optimization with select_related and prefetch_related'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('QUERY OPTIMIZATION DEMO'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Check if data exists
        if Course.objects.count() == 0:
            self.stdout.write(self.style.WARNING('\nNo data found. Please run generate_sample_data first.'))
            return
        
        # Demo 1: N+1 Problem (BAD)
        self.stdout.write(self.style.WARNING('\n\n1. N+1 PROBLEM (BAD PRACTICE)'))
        self.stdout.write('-' * 40)
        
        with CaptureQueriesContext(connection) as context:
            start_time = time.time()
            
            courses_bad = Course.objects.filter(is_published=True)[:5]
            self.stdout.write(f'\nFound {courses_bad.count()} courses')
            
            for course in courses_bad:
                # Each access triggers additional queries!
                instructor_name = course.instructor.username
                category_name = course.category.name if course.category else 'No Category'
                lessons_count = course.lessons.count()
                self.stdout.write(f'  - {course.title} by {instructor_name} ({lessons_count} lessons)')
            
            elapsed_time = (time.time() - start_time) * 1000
            
        query_count_bad = len(context.captured_queries)
        self.stdout.write(f'\n📊 Queries executed: {query_count_bad}')
        self.stdout.write(f'⏱️ Time: {elapsed_time:.2f}ms')
        self.stdout.write(f'⚠️ Problem: 1 query for courses + {courses_bad.count()} queries for related data')
        
        # Demo 2: Optimized Query (GOOD)
        self.stdout.write(self.style.SUCCESS('\n\n2. OPTIMIZED QUERY (GOOD PRACTICE)'))
        self.stdout.write('-' * 40)
        
        with CaptureQueriesContext(connection) as context:
            start_time = time.time()
            
            courses_good = Course.objects.for_listing().filter(is_published=True)[:5]
            self.stdout.write(f'\nFound {courses_good.count()} courses')
            
            for course in courses_good:
                # All data already fetched!
                instructor_name = course.instructor.username
                category_name = course.category.name if course.category else 'No Category'
                lessons_count = course.lessons_count
                self.stdout.write(f'  - {course.title} by {instructor_name} ({lessons_count} lessons)')
            
            elapsed_time = (time.time() - start_time) * 1000
            
        query_count_good = len(context.captured_queries)
        self.stdout.write(f'\n📊 Queries executed: {query_count_good}')
        self.stdout.write(f'⏱️ Time: {elapsed_time:.2f}ms')
        self.stdout.write(f'✅ Optimization: {(query_count_bad / query_count_good):.1f}x fewer queries!' if query_count_good > 0 else '✅ Optimized!')
        
        # Demo 3: Student Dashboard Query
        self.stdout.write(self.style.SUCCESS('\n\n3. STUDENT DASHBOARD QUERY (WITH PROGRESS)'))
        self.stdout.write('-' * 40)
        
        students = User.objects.filter(role='student')[:1]
        if students.exists():
            student = students.first()
            
            with CaptureQueriesContext(connection) as context:
                start_time = time.time()
                
                enrollments = Enrollment.objects.for_student_dashboard(student.id)
                
                elapsed_time = (time.time() - start_time) * 1000
                query_count = len(context.captured_queries)
                
                self.stdout.write(f'\nStudent: {student.username}')
                self.stdout.write(f'Enrollments: {enrollments.count()}')
                self.stdout.write(f'\n📊 Queries executed: {query_count}')
                self.stdout.write(f'⏱️ Time: {elapsed_time:.2f}ms')
                
                for enrollment in enrollments[:3]:
                    self.stdout.write(f'  - {enrollment.course.title}: {enrollment.progress_percentage:.1f}% complete')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY - BEST PRACTICES'))
        self.stdout.write('='*60)
        self.stdout.write('✅ Use select_related() for ForeignKey relationships')
        self.stdout.write('✅ Use prefetch_related() for ManyToMany/Reverse relationships')
        self.stdout.write('✅ Use annotate() for aggregated values')
        self.stdout.write('✅ Create custom QuerySet methods for reusable queries')
        self.stdout.write('='*60 + '\n')