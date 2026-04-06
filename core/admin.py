from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import User, Category, Course, Lesson, Enrollment, Progress, Review

# ==================== USER ADMIN ====================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'first_name', 'last_name', 'is_active', 'courses_count')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    list_select_related = ()
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'bio', 'phone', 'date_of_birth', 'profile_picture'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role',),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            courses_count=Count('courses_taught')
        )
    
    def courses_count(self, obj):
        return obj.courses_count
    courses_count.short_description = 'Courses'
    
    actions = ['make_instructor', 'make_student']
    
    def make_instructor(self, request, queryset):
        queryset.update(role='instructor')
    make_instructor.short_description = "Set as Instructor"
    
    def make_student(self, request, queryset):
        queryset.update(role='student')
    make_student.short_description = "Set as Student"


# ==================== CATEGORY ADMIN ====================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'courses_count', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_select_related = ('parent',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            courses_count=Count('courses')
        )
    
    def courses_count(self, obj):
        return obj.courses_count
    courses_count.short_description = 'Total Courses'


# ==================== LESSON INLINE ====================
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'duration_minutes', 'is_preview', 'is_published')
    ordering = ('order',)
    show_change_link = True


# ==================== COURSE ADMIN ====================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'level', 'price', 'lessons_count', 
                    'students_count', 'is_published', 'is_featured', 'thumbnail_preview')
    list_filter = ('is_published', 'is_featured', 'level', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__username', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    list_select_related = ('instructor', 'category')
    inlines = [LessonInline]
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'thumbnail_preview', 
                       'lessons_count', 'students_count')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'thumbnail', 'thumbnail_preview')
        }),
        ('Classification', {
            'fields': ('instructor', 'category', 'level')
        }),
        ('Pricing & Status', {
            'fields': ('price', 'is_published', 'is_featured', 'published_at')
        }),
        ('Statistics', {
            'fields': ('lessons_count', 'students_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('duration_hours', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            lessons_count=Count('lessons', distinct=True),
            students_count=Count('enrollments', distinct=True)
        )
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.thumbnail.url)
        return "No Image"
    thumbnail_preview.short_description = 'Preview'
    
    def lessons_count(self, obj):
        return obj.lessons_count
    lessons_count.short_description = 'Lessons'
    
    def students_count(self, obj):
        return obj.students_count
    students_count.short_description = 'Students'
    
    actions = ['publish_courses', 'unpublish_courses', 'feature_courses']
    
    def publish_courses(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} courses published.')
    publish_courses.short_description = "Publish selected courses"
    
    def unpublish_courses(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} courses unpublished.')
    unpublish_courses.short_description = "Unpublish selected courses"
    
    def feature_courses(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} courses featured.')
    feature_courses.short_description = "Feature selected courses"


# ==================== LESSON ADMIN ====================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_link', 'order', 'duration_minutes', 'is_preview', 'is_published')
    list_filter = ('is_preview', 'is_published', 'course')
    search_fields = ('title', 'content', 'course__title')
    list_select_related = ('course',)
    autocomplete_fields = ('course',)
    readonly_fields = ('created_at', 'updated_at')
    
    def course_link(self, obj):
        url = reverse('admin:core_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Course'


# ==================== ENROLLMENT ADMIN ====================
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course_link', 'enrolled_at', 'completed_at', 'is_active', 'progress_display')
    list_filter = ('is_active', 'enrolled_at', 'course')
    search_fields = ('student__username', 'course__title')
    list_select_related = ('student', 'course')
    readonly_fields = ('progress_display', 'enrolled_at')
    
    def course_link(self, obj):
        url = reverse('admin:core_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Course'
    
    def progress_display(self, obj):
        progress = obj.progress_percentage
        color = '#4CAF50' if progress >= 80 else '#FF9800' if progress >= 50 else '#f44336'
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 10px;">'
            '<div style="width: {}%; background: {}; border-radius: 10px; text-align: center; color: white;">{}%</div>'
            '</div>',
            progress, color, int(progress)
        )
    progress_display.short_description = 'Progress'
    
    actions = ['mark_completed']
    
    def mark_completed(self, request, queryset):
        for enrollment in queryset:
            enrollment.complete()
        self.message_user(request, f'{queryset.count()} enrollments marked as completed.')
    mark_completed.short_description = "Mark as completed"


# ==================== PROGRESS ADMIN ====================
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'lesson_title', 'is_completed', 'completed_at', 'last_accessed', 'time_spent_display')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('enrollment__student__username', 'lesson__title')
    list_select_related = ('enrollment', 'enrollment__student', 'lesson')
    readonly_fields = ('time_spent_display',)
    
    def student_name(self, obj):
        return obj.enrollment.student.username
    student_name.short_description = 'Student'
    
    def lesson_title(self, obj):
        return obj.lesson.title
    lesson_title.short_description = 'Lesson'
    
    def time_spent_display(self, obj):
        minutes = obj.time_spent_seconds // 60
        seconds = obj.time_spent_seconds % 60
        return f"{minutes}m {seconds}s"
    time_spent_display.short_description = 'Time Spent'


# ==================== REVIEW ADMIN ====================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'rating', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('course__title', 'student__username', 'comment')
    list_select_related = ('course', 'student')
    readonly_fields = ('created_at', 'updated_at')
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'