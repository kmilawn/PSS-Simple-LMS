from celery import shared_task
from django.core.cache import cache
from datetime import datetime
import csv
import os

from .mongodb import activity_logs
from .models import Course

@shared_task
def send_enrollment_email(username, course_title):
    """Send enrollment confirmation email (simulated)"""
    
    message = f"Email sent to {username} for enrolling in {course_title}"
    
    print(f"[EMAIL TASK] {message}")
    
    activity_logs.insert_one({
        "task": "send_enrollment_email",
        "username": username,
        "course": course_title,
        "message": message,
        "timestamp": datetime.utcnow()
    })
    
    return message

@shared_task
def generate_certificate(username, course_title):
    """Generate certificate for completed course"""
    
    message = f"Certificate generated for {username} - {course_title}"
    
    print(f"[CERTIFICATE TASK] {message}")
    
    activity_logs.insert_one({
        "task": "generate_certificate",
        "username": username,
        "course": course_title,
        "message": message,
        "timestamp": datetime.utcnow()
    })
    
    return message

@shared_task
def update_course_statistics():
    """Update course statistics periodically"""
    
    courses = Course.objects.all()
    
    stats = []
    for course in courses:
        enrollment_count = course.enrollments.count()
        lesson_count = course.lessons.count()
        
        stats.append({
            "course_id": course.id,
            "title": course.title,
            "enrollments": enrollment_count,
            "lessons": lesson_count
        })
        
        print(f"[STATS] {course.title} -> {enrollment_count} enrollments")
    
    activity_logs.insert_one({
        "task": "update_course_statistics",
        "message": "Statistics Updated",
        "stats": stats,
        "timestamp": datetime.utcnow()
    })
    
    # Clear course list cache
    cache.clear()
    
    return "Statistics Updated"

@shared_task
def export_course_report():
    """Export course data to CSV"""
    
    path = "/tmp/course_report.csv"
    
    with open(path, "w", newline="", encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Course ID", "Course Title", "Students Enrolled", "Lessons Count", "Is Published"])
        
        for course in Course.objects.all():
            writer.writerow([
                course.id,
                course.title,
                course.enrollments.count(),
                course.lessons.count(),
                course.is_published
            ])
    
    activity_logs.insert_one({
        "task": "export_course_report",
        "message": f"Report exported to {path}",
        "timestamp": datetime.utcnow()
    })
    
    return path