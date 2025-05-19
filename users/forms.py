from django import forms
from exams.models import Message
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import GPASemester, CourseGrade, UserProfile, LiveClass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
import pytz
from django.utils import timezone


class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(queryset=User.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = Message
        fields = ['content', 'receiver']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4, 'placeholder': 'Type your message...'}),
        }


class GPASemesterForm(forms.ModelForm):
    class Meta:
        model = GPASemester
        fields = ['name']

class CourseGradeForm(forms.ModelForm):
    class Meta:
        model = CourseGrade
        fields = ['course_name', 'grade', 'credit_units']


User = get_user_model()

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded'}),
        strip=False,
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded'}),
        strip=False,
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get("old_password")
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Your old password was entered incorrectly.")
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn’t match.")
        if new_password1:
            validate_password(new_password1, self.user)
        return new_password2

    def save(self):
        new_password = self.cleaned_data["new_password1"]
        self.user.set_password(new_password)
        self.user.save()
        return self.user

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'w-full p-2 border rounded'}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No user is associated with this email address.")
        return email

class PasswordResetConfirmForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full p-2 border rounded'}),
        strip=False,
    )

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("The two password fields didn’t match.")
        if new_password1:
            validate_password(new_password1)
        return new_password2
    
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Enter your email'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Enter your first name'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Enter your first name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Enter your email'})
    )

    class Meta:
        model = UserProfile
        fields = ('profile_image', 'bio', 'user_type')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'w-full border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 4, 'placeholder': 'Tell us about yourself'}),
            'user_type': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'profile_image': forms.FileInput(attrs={'class': 'w-full border border-gray-300 rounded p-2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile
    
class LiveClassForm(forms.ModelForm):
    class Meta:
        model = LiveClass
        fields = ['title', 'description', 'meet_link', 'scheduled_at']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'mt-1 block w-full border-gray-300 rounded-lg'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'mt-1 block w-full border-gray-300 rounded-lg'}),
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-lg'}),
            'meet_link': forms.URLInput(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-lg'}),
        }

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data['scheduled_at']
        print(f"Raw scheduled_at: {scheduled_at}")  # Debug
        wat_timezone = pytz.timezone('Africa/Lagos')
        if not timezone.is_aware(scheduled_at):
            scheduled_at = wat_timezone.localize(scheduled_at)
        scheduled_at_utc = scheduled_at.astimezone(pytz.UTC)
        print(f"Converted to UTC: {scheduled_at_utc}")  # Debug
        if scheduled_at_utc < timezone.now():
            raise forms.ValidationError("Cannot schedule a class in the past.")
        return scheduled_at_utc