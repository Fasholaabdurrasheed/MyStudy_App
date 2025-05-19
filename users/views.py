from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import GPASemester, CourseGrade, LiveClass
from .forms import GPASemesterForm, CourseGradeForm, PasswordChangeForm, PasswordResetRequestForm, PasswordResetConfirmForm, CustomUserCreationForm, UserProfileForm, LiveClassForm
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
from django.utils import timezone

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_mail(
    'Welcome to MyStudy_App!',
    f'Hello {user.first_name}, your account was created successfully!',
    'mystudyapp.unilorin@gmail.com',
    [user.email],
    fail_silently=False,
)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('users:signup_success')  # Redirect to success view
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/signup.html', {'form': form})

def signup_success(request):
    return render(request, 'users/signup_success.html')

@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('users:profile')  # Redirect to profile view after saving
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'users/profile_edit.html', {'form': form})


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
            try:
                user = User.objects.get(email=email)
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    f"/users/reset/{uid}/{token}/"
                )
                subject = "Password Reset Request - MyStudy App"
                # Render HTML email
                html_message = render_to_string(
                    "registration/password_reset_email.html",
                    {
                        "user": user,
                        "protocol": "https" if request.is_secure() else "http",
                        "domain": request.get_host(),
                        "uid": uid,
                        "token": token,
                        "password_reset_timeout": 24,  # Adjust based on your settings
                    },
                )
                # Render plain text fallback
                plain_message = render_to_string(
                    "registration/password_reset_email.txt",
                    {
                        "user": user,
                        "protocol": "https" if request.is_secure() else "http",
                        "domain": request.get_host(),
                        "uid": uid,
                        "token": token,
                        "password_reset_timeout": 24,
                    },
                )
                send_mail(
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(
                    request, "A password reset link has been sent to your email."
                )
                return redirect("login")
            except User.DoesNotExist:
                messages.error(request, "No user found with this email address.")
            except Exception as e:
                messages.error(request, f"Failed to send email: {e}")
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

def is_teacher(user):
    return user.is_staff

@login_required
@user_passes_test(is_teacher)
def create_live_class(request):
    if request.method == 'POST':
        form = LiveClassForm(request.POST)
        if form.is_valid():
            live_class = form.save(commit=False)
            live_class.teacher = request.user
            live_class.save()
            try:
                students = User.objects.filter(is_staff=False)
                recipient_list = [student.email for student in students if student.email]
                if recipient_list:
                    for student in students:
                        if student.email:
                            html_message = render_to_string('emails/live_class_notification.html', {
                                'recipient_name': student.get_full_name() or student.username,
                                'class_title': live_class.title,
                                'scheduled_at': live_class.scheduled_at,
                                'meet_link': live_class.meet_link,
                                'subject': f'New Live Class: {live_class.title}',
                            })
                            plain_message = render_to_string('emails/live_class_notification.txt', {
                                'recipient_name': student.get_full_name() or student.username,
                                'class_title': live_class.title,
                                'scheduled_at': live_class.scheduled_at,
                                'meet_link': live_class.meet_link,
                            })
                            send_mail(
                                subject=f'New Live Class: {live_class.title}',
                                message=plain_message,
                                html_message=html_message,
                                from_email='mystudyapp.unilorin@gmail.com',
                                recipient_list=[student.email],
                                fail_silently=False,
                            )
                    messages.success(request, 'Live class created and students notified.')
                else:
                    messages.warning(request, 'Live class created, but no students with valid emails found.')
            except Exception as e:
                messages.error(request, f'Live class created, but failed to send email: {e}')
            return redirect('users:live_classes')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LiveClassForm()
    return render(request, 'users/create_live_class.html', {'form': form})
@login_required
def live_classes_list(request):
    classes = LiveClass.objects.all().order_by('scheduled_at')
    if not request.user.is_staff:  # Students see only upcoming/live classes
        classes = classes.filter(scheduled_at__gte=timezone.now() - timezone.timedelta(hours=1))
    return render(request, 'users/live_classes.html', {'classes': classes})

