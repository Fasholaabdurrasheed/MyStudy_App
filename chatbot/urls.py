from django.urls import path
from .views import chatbot_response
from django.views.generic import TemplateView

urlpatterns = [
    path('chatbot/', chatbot_response, name='chatbot_response'),
]

urlpatterns += [
    path('studybot/', TemplateView.as_view(template_name='chatbot.html'), name='chatbot_ui'),
]

