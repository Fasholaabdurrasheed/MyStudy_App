from .models import CourseEnrollment, Message

def default_course_context(request):
    if request.user.is_authenticated:
        try:
            enrollment = CourseEnrollment.objects.filter(user=request.user).first()
            if enrollment:
                return {'default_course_id': enrollment.course.id}
        except CourseEnrollment.DoesNotExist:
            pass
    return {'default_course_id': None}

def unread_message_count(request):
    count = 0
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return {'unread_count': count}
    return{}