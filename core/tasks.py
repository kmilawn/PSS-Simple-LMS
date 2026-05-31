from celery import shared_task
from pymongo import MongoClient
from .models import Course
import csv
import os

client = MongoClient("mongodb://mongodb:27017/")
db = client["simple_lms"]

@shared_task
def send_enrollment_email(username, course_title):

    message = f"Email sent to {username} for enrolling in {course_title}"

    print(message)

    db.activity_logs.insert_one({
        "task": "send_enrollment_email",
        "username": username,
        "course": course_title,
        "message": message
    })

    return message


@shared_task
def generate_certificate(username, course_title):

    message = f"Certificate generated for {username} - {course_title}"

    print(message)

    db.activity_logs.insert_one({
        "task": "generate_certificate",
        "username": username,
        "course": course_title,
        "message": message
    })

    return message


@shared_task
def update_course_statistics():

    courses = Course.objects.all()

    for course in courses:
        count = course.enrollments.count()

        print(f"{course.title} -> {count}")

    db.activity_logs.insert_one({
        "task": "update_course_statistics",
        "message": "Statistics Updated"
    })

    return "Statistics Updated"

@shared_task
def export_course_report():
    path = "/tmp/course_report.csv"

    with open(path, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow(["Course", "Students"])

        for course in Course.objects.all():
            writer.writerow([
                course.title,
                course.enrollments.count()
            ])

    db.activity_logs.insert_one({
        "task": "export_course_report",
        "message": f"Report exported to {path}"
    })

    return path