from django.urls import path
from .views import signup_view, profile_view
from django.contrib.auth.views import LoginView

app_name = 'users'

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
]
