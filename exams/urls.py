from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from exams.views import serve_media

app_name = 'exams'

urlpatterns = [
    path('join-course/', views.join_course_view, name='join_course'),
    path('my-courses/', views.my_courses_view, name='my_courses'),
    path('leave-course/<int:course_id>/', views.leave_course_view, name='leave_course'),
    path('course/<int:course_id>/materials/', views.course_materials_view, name='course_materials'),
    path('course/<int:course_id>/upload-material/', views.upload_course_material, name='upload_material'),
    path('materials/preview/<int:material_id>/', views.material_preview, name='material_preview'),
    path('materials/<int:material_id>/', views.material_detail, name='material_detail'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/exams/', views.available_exams, name='available_exams'),
    path('exam/<int:exam_id>/start/', views.start_exam, name='start_exam'),
    path('exam/<int:exam_id>/result/', views.exam_result, name='exam_result'),
    path('exam/<int:exam_id>/review/', views.review_answers, name='review_answers'),
    path('media/<path:path>', serve_media, name='serve_media'),
    path('inbox/', views.inbox, name='inbox'),
    path('chat/<str:username>/', views.chat_view, name='chat_view'),
    path('tutors/', views.tutor_list, name='tutor_list'),
    path('messages/<int:user_id>/', views.view_message, name='view_message'),
    path('materials/', views.materials_list, name='materials'),
    # path('exams/', views.exams_list, name='exams'),
    path('performance/', views.performance, name='performance'),
    path('exam/<int:exam_id>/upload-questions/', views.bulk_upload_questions, name='bulk_upload_questions'),
    path('exam/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('courses/', views.list_courses, name='list_courses'),
    path('courses/<int:course_id>/enroll/', views.enroll_in_course, name='enroll_in_course'),
    path('my-exams/', views.exam_panel, name='exam_panel'),
    path('exam/<int:exam_id>/submit/', views.submit_exam, name='submit_exam'),
    # path('past-questions/', views.student_past_questions, name='student_past_questions'),
    path('past-questions/', views.past_questions, name='past_questions'),
    path('upload-question/', views.upload_past_question, name='upload_past_question'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)