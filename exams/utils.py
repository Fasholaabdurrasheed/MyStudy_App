from .models import CourseExam, Course, CourseQuestion

def get_dropdown_data():
    return {
        'exams': CourseExam.objects.all(),
        'courses': Course.objects.all(),
        'questions': CourseQuestion.objects.all(),
    }
