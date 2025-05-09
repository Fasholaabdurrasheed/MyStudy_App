from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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

# Combined safe signal
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


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
