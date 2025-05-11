from django.db import models
from django.contrib.auth.models import User

class Faculty(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"

class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=200)  # E.g., 'Mathematics', 'Biology'
    year = models.PositiveIntegerField()
    code = models.CharField(max_length=20)
    exam_type = models.CharField(max_length=50, choices=[
        ('FIRST_SEMESTER', 'FIRST SEMESTER'),
        ('SECOND_SEMESTER', 'SECOND SEMESTER'),
        ('CA_TEST', 'CA_TEST'),
    ])

    def __str__(self):
        return f"{self.code} - {self.name}"

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_students')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')  # Prevent duplicate enrollments

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.name}"

class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_materials')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='course_materials/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course.name})"

class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='materials/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CourseExam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    name = models.CharField(max_length=200)
    num_questions = models.PositiveIntegerField()
    time_limit = models.PositiveIntegerField(help_text="Time limit in minutes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.name} - {self.name}"

class CourseQuestion(models.Model):
    exam = models.ForeignKey(CourseExam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])

    def __str__(self):
        return f"Question for {self.exam.name}"

class CourseAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(CourseQuestion, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.question.exam.name}"

class CourseExamAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(CourseExam, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    correct_answers = models.IntegerField(null=True, blank=True)
    total_questions = models.IntegerField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} - {self.exam.name} ({self.score if self.score is not None else 'N/A'}%)"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} to {self.recipient.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} at {self.timestamp}"


class ExamSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(CourseExam, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'exam')

    def __str__(self):
        return f"{self.user.username} - {self.exam.name}"


class PastQuestionFile(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=20, choices=[('WAEC', 'WAEC'), ('NECO', 'NECO'), ('JAMB', 'JAMB')])
    year = models.IntegerField()
    file = models.FileField(upload_to='pastquestions/')  # for PDF or docs
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.name} - {self.exam_type} {self.year}"
