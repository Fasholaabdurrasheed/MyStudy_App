from django import forms
from .models import Faculty, Department, Course, CourseEnrollment, CourseMaterial, Material
from .models import CourseExam, CourseQuestion, CourseAnswer, CourseExamAttempt, Message, CourseEnrollment
import csv
from io import TextIOWrapper
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages


class QuestionUploadForm(forms.Form):
    csv_file = forms.FileField()



@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty')
    search_fields = ('name', 'faculty__name')
    list_filter = ('faculty',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'year', 'exam_type')
    search_fields = ('name', 'subject', 'department__name')
    list_filter = ('department', 'exam_type', 'year')

# @admin.register(StudentCourse)
# class StudentCourse(admin.ModelAdmin):
#     list_display = ('user', 'course', 'joined_at')
#     search_fields = ('user__username', 'course__name')
#     list_filter = ('joined_at',)

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_at')
    search_fields = ('title', 'course__name')

@admin.register(Material)   
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_by', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description')


@admin.register(CourseExam)
class CourseExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'num_questions', 'time_limit')

@admin.register(CourseQuestion)
class CourseQuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'text')

@admin.register(CourseAnswer)
class CourseAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'is_correct', 'answered_at')


@admin.register(CourseExamAttempt)
class CourseExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'exam', 'score', 'passed', 'started_at')
    list_filter = ('exam', 'passed', 'started_at')
    search_fields = ('user__username', 'exam__name')
    ordering = ('-started_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read')
    search_fields = ('sender__username', 'receiver__username', 'content')

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')  # corrected field name
    search_fields = ('user__username', 'course__name')
    list_filter = ('course',)  

admin.site.site_header = "Exams Admin"
admin.site.site_title = "MyStudy_App"
admin.site.index_title = "Welcome to the  Admin Portal"
