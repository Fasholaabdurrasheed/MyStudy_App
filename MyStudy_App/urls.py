"""
URL configuration for MyStudy_App project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
# from exams import views as exam_views
from exams import views




urlpatterns = [
    path('admin/', admin.site.urls),
    path('exams/', include('exams.urls')),
    path('users/', include('users.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    
    # Include the default authentication URLs (login, logout, password change, etc.)
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('inbox/<int:user_id>/', views.view_message, name='view_message'),
    # path('messages/', include('messaging.urls')),
    # path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('bot/', include('chatbot.urls')),
     

]

# project-level urls.py
from django.conf import settings
from django.urls import re_path
from exams.views import serve_media  # adjust path if needed

if settings.DEBUG:
    # For development: serve using Django's static() helper
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # For production: custom view to serve media files
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media),
    ]
