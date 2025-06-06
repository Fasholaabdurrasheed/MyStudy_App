# MyStudy_App/users/urls.py
from django.urls import path
from .views import signup_view, profile_view
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', signup_view, name='signup'),
     path('signup/success/', views.signup_success, name='signup_success'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('create/', views.create_live_class, name='create_live_class'),
    path('live/', views.live_classes_list, name='live_classes'),
    # PASSWORD RESET
    path("password/change/", views.password_change, name="password_change"),
    path("password/reset/", views.password_reset_request, name="password_reset"),
    path("reset/<uidb64>/<token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path('gpa/', views.gpa_home, name='gpa_home'),
    path('gpa/add/', views.add_semester, name='add_semester'),
]