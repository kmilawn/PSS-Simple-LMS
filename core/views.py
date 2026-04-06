from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return HttpResponse("<h1>Welcome to Simple LMS</h1><p>Your Learning Management System is running!</p>")

def welcome(request):
    return render(request, 'welcome.html')