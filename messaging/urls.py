# messaging/urls.py
from django.urls import path
from exams import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('messages/<int:user_id>/', views.view_message, name='view_message'),
    # path('reply/<int:user_id>/', views.reply_message, name='reply_message'),
]
