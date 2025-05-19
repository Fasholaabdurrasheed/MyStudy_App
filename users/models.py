from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from django.utils import timezone

def user_profile_path(instance, filename):
    return f'profile_images/user_{instance.user.id}/{filename}'

class UserProfile(models.Model):
    USER_TYPES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to=user_profile_path, default='default_avatar.png', blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='student')
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

GRADE_CHOICES = [
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
    ('F', 'F'),
]

GRADE_POINTS = {
    'A': 5.0,
    'B': 4.0,
    'C': 3.0,
    'D': 2.0,
    'E': 1.0,
    'F': 0.0,
}

class GPASemester(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g., "2023/2024 - Semester 1"
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_gpa(self):
        courses = self.courses.all()
        total_units = sum(course.credit_units for course in courses)
        total_points = sum(course.credit_units * GRADE_POINTS[course.grade] for course in courses)
        return round(total_points / total_units, 2) if total_units > 0 else 0

class CourseGrade(models.Model):
    semester = models.ForeignKey(GPASemester, on_delete=models.CASCADE, related_name='courses')
    course_name = models.CharField(max_length=100)
    grade = models.CharField(max_length=1, choices=GRADE_CHOICES)
    credit_units = models.PositiveIntegerField()

class LiveClass(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meet_link = models.URLField(
        validators=[
            RegexValidator(
                regex=r'^https://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}$',
                message='Enter a valid Google Meet link (e.g., https://meet.google.com/abc-defg-hij)',
            )
        ]
    )
    scheduled_at = models.DateTimeField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title

    def get_status(self):
        now = timezone.now()
        if now < self.scheduled_at:
            return "Upcoming"
        elif now < self.scheduled_at + timezone.timedelta(hours=1):  # Assume 1-hour duration
            return "Live"
        else:
            return "Ended"