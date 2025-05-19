from django.contrib import admin

from django.contrib import admin
from .models import UserProfile, LiveClass

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')

@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'scheduled_at', 'meet_link')
    search_fields = ('title', 'teacher__username')
    list_filter = ('scheduled_at',)