from django import template
from exams.models import CourseEnrollment, CourseExam


register = template.Library()

@register.filter
def get_option_text(question, option):
    return getattr(question, f'option_{option.lower()}')


@register.simple_tag
def get_exam_course_id(user):
    if user.is_authenticated:
        enrolled_courses = CourseEnrollment.objects.filter(user=user).values_list('course_id', flat=True)
        # Find the first course with an exam
        course_exam = CourseExam.objects.filter(course_id__in=enrolled_courses).first()
        if course_exam:
            return course_exam.course.id
    return None