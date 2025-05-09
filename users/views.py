from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .models import GPASemester, CourseGrade
from .forms import GPASemesterForm, CourseGradeForm, PasswordChangeForm, PasswordResetRequestForm, PasswordResetConfirmForm
from django.forms import modelformset_factory
import plotly.graph_objects as go
import plotly
from django.utils.safestring import mark_safe
import json
from django.contrib.auth import get_user_model, login
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile is created automatically via post_save signal
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('exams:inbox')  # Redirect to inbox after signup
    else:
        form = UserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})


def gpa_home(request):
    semesters = GPASemester.objects.filter(user=request.user)
    
    labels = [s.name for s in semesters]
    values = [s.calculate_gpa() for s in semesters]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=values, mode='lines+markers', name='GPA'))
    fig.update_layout(
        title='GPA Progression Over Time',
        xaxis_title='Semester',
        yaxis_title='GPA',
        yaxis=dict(range=[0, 5]),
        template='plotly_white'
    )
    chart_json = mark_safe(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder))

    return render(request, 'gpa/gpa_home.html', {
        'semesters': semesters,
        'chart': chart_json
    })


def add_semester(request):
    CourseFormSet = modelformset_factory(CourseGrade, form=CourseGradeForm, extra=1, can_delete=True)

    if request.method == 'POST':
        semester_form = GPASemesterForm(request.POST)
        course_formset = CourseFormSet(request.POST, queryset=CourseGrade.objects.none())

        if semester_form.is_valid() and course_formset.is_valid():
            semester = semester_form.save(commit=False)
            semester.user = request.user
            semester.save()
            for form in course_formset:
                course = form.save(commit=False)
                course.semester = semester
                course.save()
            return redirect('users:gpa_home')

    else:
        semester_form = GPASemesterForm()
        course_formset = CourseFormSet(queryset=CourseGrade.objects.none())

    return render(request, 'gpa/add_semester.html', {
        'semester_form': semester_form,
        'course_formset': course_formset,
    })


User = get_user_model()

@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Re-authenticate the user to update the session
            login(request, request.user)
            messages.success(request, "Your password was successfully changed!")
            return redirect("users:profile")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "users/password_change.html", {"form": form})

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.get(email=email)
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                f"/users/reset/{uid}/{token}/"
            )
            subject = "Password Reset Request"
            message = render_to_string(
                "users/password_reset_email.html",
                {
                    "user": user,
                    "reset_url": reset_url,
                },
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(
                request, "A password reset link has been sent to your email."
            )
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordResetRequestForm()
    return render(request, "users/password_reset_request.html", {"form": form})

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if user is not None and token_generator.check_token(user, token):
        if request.method == "POST":
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data["new_password1"])
                user.save()
                messages.success(request, "Your password has been reset. You can now log in.")
                return redirect("login")
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = PasswordResetConfirmForm()
        return render(request, "users/password_reset_confirm.html", {"form": form})
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect("users:password_reset")