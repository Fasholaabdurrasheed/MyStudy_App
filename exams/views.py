from django.shortcuts import render, redirect, get_object_or_404
from .models import CourseExam, CourseQuestion, CourseAnswer, CourseExamAttempt, Announcement, Message, CourseEnrollment
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string, get_template
import random
from django.utils import timezone
from django.utils.timezone import now
from datetime import datetime, timedelta
from .models import Faculty, Department, Course, CourseEnrollment, CourseMaterial, Material, ExamSubmission, PastQuestionFile
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from .forms import MaterialUploadForm, PastQuestionUploadForm
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import FileResponse, HttpResponseNotFound
import os
from django.conf import settings
from .forms import MessageForm, BulkQuestionUploadForm, CourseQuestionForm
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.db.models import Max, Q, Count, Avg 
from django.http import JsonResponse
import json
import pandas as pd
from django.views.decorators.http import require_POST


@login_required
def materials_list(request):
    # Get enrolled course IDs
    enrolled_course_ids = CourseEnrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
    
    # Get course objects
    enrolled_courses = Course.objects.filter(id__in=enrolled_course_ids)

    # Get materials for enrolled courses
    materials = Material.objects.filter(course__id__in=enrolled_course_ids).order_by('-created_at')

    return render(request, 'materials/material_list.html', {
        'materials': materials,
        'enrolled_courses': enrolled_courses,
    })

# @login_required
# def exams_list(request):
#     # Get exams for courses the user is enrolled in
#     enrolled_courses = CourseEnrollment.objects.filter(user=request.user).values_list('course_id', flat=True)
#     exams = CourseExam.objects.filter(course__id__in=enrolled_courses)
#     return render(request, 'exams/exams_list.html', {'exams': exams})

@login_required
def performance(request):
    answers = CourseAnswer.objects.filter(user=request.user)
    exams = CourseExam.objects.filter(
        questions__courseanswer__user=request.user
    ).distinct()

    results = []
    for exam in exams:
        exam_answers = answers.filter(question__exam=exam)
        total_questions = exam.num_questions
        correct_answers = exam_answers.filter(is_correct=True).count()
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        results.append({
            'exam': exam,
            'score': round(score, 1),
            'passed': score >= 50,
        })

    return render(request, 'exams/performance.html', {'results': results})

@login_required
def join_course_view(request):
    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    courses = Course.objects.all()
    
    selected_faculty = request.GET.get('faculty')
    selected_department = request.GET.get('department')

    if selected_faculty:
        departments = Department.objects.filter(faculty_id=selected_faculty)
    
    if selected_department:
        courses = Course.objects.filter(department_id=selected_department)

    if request.method == "POST":
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)

        # Prevent joining twice
        CourseEnrollment.objects.get_or_create(user=request.user, course=course)
        messages.success(request, f"You have successfully joined {course.name}!")

        return redirect('exams:my_courses')  # Redirect to my courses after joining

    context = {
        'faculties': faculties,
        'departments': departments,
        'courses': courses,
        'selected_faculty': selected_faculty,
        'selected_department': selected_department,
    }
    return render(request, "exams/join_course.html", context)

@login_required
def my_courses_view(request):
    my_courses = CourseEnrollment.objects.filter(user=request.user)

    return render(request, "exams/my_courses.html", {
        'my_courses': my_courses
    })

@login_required
def course_materials_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Ensure the user is enrolled!
    if not CourseEnrollment.objects.filter(user=request.user, course=course).exists():
        return redirect('exams:my_courses')  # Or show a permission denied page
    
    materials = Material.objects.filter(course=course).order_by('-created_at')
    return render(request, 'exams/course_materials.html', {
        'course': course,
        'materials': materials
    })

@login_required
def leave_course_view(request, course_id):
    try:
        enrollment = CourseEnrollment.objects.get(user=request.user, course_id=course_id)
        enrollment.delete()
    except CourseEnrollment.DoesNotExist:
        pass  # If not enrolled, do nothing

    return redirect('exams:my_courses')

@staff_member_required
def upload_course_material(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        link = request.POST.get('link')

        CourseMaterial.objects.create(
            course=course,
            title=title,
            description=description,
            file=file,
            link=link
        )
        return redirect('exams:course_materials', course_id=course.id)

    return render(request, 'exams/upload_materials.html', {'course': course})

@login_required
def material_preview(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    return render(request, 'materials/material_preview.html', {'material': material})

@login_required
def upload_materials(request):
    if request.method == 'POST':
        form = MaterialUploadForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.cleaned_data['course']
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            file = form.cleaned_data['file']

            Material.objects.create(
                course=course,
                uploaded_by=request.user,
                file=file,
                title=title,
                description=description,
            )

            return redirect('exams:materials')
    else:
        form = MaterialUploadForm()

    return render(request, 'exams/upload_materials.html', {'form': form})

@login_required
def material_detail(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    
    # Detect if the file is a PDF
    is_pdf = material.file.url.endswith('.pdf') if material.file else False
    
    # Compute the absolute URI for the file
    absolute_file_url = request.build_absolute_uri(material.file.url) if material.file else None

    return render(request, "exams/material_detail.html", {
        "material": material,
        "is_pdf": is_pdf,
        "absolute_file_url": absolute_file_url,
    })

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_joined = CourseEnrollment.objects.filter(user=request.user, course=course).exists()

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'is_joined': is_joined,
    })

@login_required
def available_exams(request):
    # Get all courses the user is enrolled in
    enrolled_courses = CourseEnrollment.objects.filter(user=request.user).values_list('course', flat=True)
    courses = Course.objects.filter(id__in=enrolled_courses)
    
    # Get all exams for enrolled courses
    exams = CourseExam.objects.filter(course__in=courses)
    
    # Prepare data for template (group exams by course if needed)
    course_exams = {}
    for course in courses:
        course_exams[course] = exams.filter(course=course)
    
    return render(request, 'exams/available_exams.html', {
        'course_exams': course_exams,
    })

@login_required
def start_exam(request, exam_id):
    exam = get_object_or_404(CourseExam, id=exam_id)
    questions = list(CourseQuestion.objects.filter(exam=exam).order_by('id'))
    total_questions = len(questions)

    # Get or create attempt
    exam_attempt = CourseExamAttempt.objects.filter(
    user=request.user,
    exam=exam,
    completed_at__isnull=True
    ).first()

    if not exam_attempt:
        exam_attempt = CourseExamAttempt.objects.create(
        user=request.user,
        exam=exam,
        started_at=timezone.now()
    )

    # Index tracking
    current_index = int(request.POST.get("current_index", 0))

    # Save selected answer
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        selected_option = request.POST.get("selected_option")

        if question_id and selected_option:
            question = get_object_or_404(CourseQuestion, id=question_id)

            # Save or update answer
            answer, created = CourseAnswer.objects.update_or_create(
                user=request.user,
                question=question,
                defaults={
                    "selected_option": selected_option,
                    "is_correct": selected_option == question.correct_option
                }
            )

        # Navigation
        if "next" in request.POST and current_index < total_questions - 1:
            current_index += 1
        elif "prev" in request.POST and current_index > 0:
            current_index -= 1
        elif "submit_exam" in request.POST:
            return redirect('exams:submit_exam', exam_id=exam.id)

    # Time left
    end_time = exam_attempt.started_at + timedelta(minutes=exam.time_limit)
    time_left = int((end_time - timezone.now()).total_seconds())

    # Auto-submit if time is up (hard backend stop)
    if time_left <= 0:
        exam_attempt.completed_at = timezone.now()
        exam_attempt.save()
        return redirect('exams:submit_exam', exam_id=exam.id)


    current_question = questions[current_index]
    selected_option = CourseAnswer.objects.filter(user=request.user, question=current_question).first()

    context = {
        "exam": exam,
        "total_questions": total_questions,
        "current_index": current_index,
        "current_question": current_question,
        "selected_option": selected_option.selected_option if selected_option else None,
        "time_left": time_left,
        "time_limit": time_left
    }

    return render(request, "exams/start_exam.html", context)

@login_required
def submit_exam(request, exam_id):
    exam = get_object_or_404(CourseExam, id=exam_id)

    # Try to get an ongoing attempt, fallback to last if not
    exam_attempt = CourseExamAttempt.objects.filter(user=request.user, exam=exam).last()
    if not exam_attempt or exam_attempt.completed_at:
        messages.error(request, "You have already submitted this exam or haven't started it.")
        return redirect('exams:available_exams', course_id=exam.course.id)

    answers = CourseAnswer.objects.filter(user=request.user, question__exam=exam)
    total_questions = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    submission = ExamSubmission.objects.create(
        user=request.user,
        exam=exam,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_answers
    )

    exam_attempt.score = score
    exam_attempt.correct_answers = correct_answers
    exam_attempt.total_questions = total_questions
    exam_attempt.passed = score >= 50
    exam_attempt.completed_at = timezone.now()
    exam_attempt.save()

    stroke_offset = 282 - (score / 100 * 282)

    return render(request, 'exams/exam_result.html', {
        'submission': submission,
        'exam': exam,
        'exam_id': exam.id,
        'score': round(score, 2),
        'passed': score >= 50,
        'stroke_offset': stroke_offset
    })



def exam_result(request, exam_id):
    exam = get_object_or_404(CourseExam, id=exam_id)
    answers = CourseAnswer.objects.filter(user=request.user, question__exam=exam)

    # Calculate score
    total_questions = exam.num_questions
    correct_answers = answers.filter(is_correct=True).count()
    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0

    # Determine pass/fail
    passed = score >= 50

    # Save or update the ExamSubmission
    submission, created = ExamSubmission.objects.update_or_create(
        user=request.user,
        exam=exam,
        defaults={
            'score': score,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
        }
    )

    # Calculate stroke offset for SVG circle animation
    stroke_offset = 282 * (1 - score / 100)

    return render(request, 'exams/exam_result.html', {
        'exam': exam,
        'exam_id': exam_id,
        'course_id': exam.course.id,
        'score': round(score, 1),
        'passed': passed,
        'stroke_offset': stroke_offset,
    })

@login_required
def review_answers(request, exam_id):
    exam = get_object_or_404(CourseExam, id=exam_id)
    answers = CourseAnswer.objects.filter(user=request.user, question__exam=exam)

    # Calculate mark per question
    total_questions = answers.count()
    question_mark = 100 / total_questions if total_questions > 0 else 0

    return render(request, 'exams/review_answers.html', {
        'exam': exam,
        'answers': answers,
        'question_mark': round(question_mark, 2),
        'course_id': exam.course.id,
    })

@xframe_options_exempt
def serve_media(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))
    else:
        return HttpResponseNotFound("File not found")


@login_required
def inbox(request):
    user = request.user

    # Get all messages involving the user
    messages = Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-timestamp')

    # Track the latest message per conversation
    conversations = {}
    for msg in messages:
        # Identify the other user in the conversation
        other_user = msg.receiver if msg.sender == user else msg.sender
        if other_user not in conversations:
            conversations[other_user] = msg  # First one is the latest because of .order_by('-timestamp')

    # Sort by latest message timestamp
    sorted_conversations = sorted(conversations.values(), key=lambda m: m.timestamp, reverse=True)

    unread_count = Message.objects.filter(receiver=user, is_read=False).count()

    # Fetch all users except the current user for the empty state
    available_users = User.objects.exclude(id=user.id)

    return render(request, 'messaging/inbox.html', {
        'messages': sorted_conversations,
        'unread_count': unread_count,
        'total_count': len(sorted_conversations),
        'active_user': user,
        'available_users': available_users,  # New context variable
    })

# Other views remain unchanged
@login_required
def chat_view(request, username):
    tutor = get_object_or_404(User, username=username)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=tutor) | Q(sender=tutor, receiver=request.user)
    ).order_by('timestamp')

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = tutor
            message.is_read = False
            message.save()
            return redirect('exams:chat_view', username=tutor.username)
    else:
        form = MessageForm(initial={'receiver': tutor.pk})

    return render(request, 'messaging/chat.html', {
        'form': form,
        'messages': messages,
        'tutor': tutor
    })

@login_required
def tutor_list(request):
    try:
        tutor_group = Group.objects.get(name="Tutor")
    except Group.DoesNotExist:
        tutor_group = Group.objects.create(name="Tutor")

    query = request.GET.get("q", "")
    filter_my_chats = request.GET.get("mine") == "1"

    tutors = tutor_group.user_set.all()

    if query:
        tutors = tutors.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

    if filter_my_chats:
        chatted_ids = Message.objects.filter(sender=request.user).values_list('receiver', flat=True).distinct()
        tutors = tutors.filter(id__in=chatted_ids)

    tutor_data = []
    for tutor in tutors:
        last_message = Message.objects.filter(
            Q(sender=request.user, receiver=tutor) |
            Q(sender=tutor, receiver=request.user)
        ).order_by('-timestamp').first()
        tutor_data.append({
            'user': tutor,
            'last_message': last_message
        })

    return render(request, 'messaging/tutor_list.html', {
        'tutors': tutor_data,
        'query': query,
        'filter_my_chats': filter_my_chats,
    })

@login_required
def view_message(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    messages = Message.objects.filter(
        sender__in=[request.user, other_user],
        receiver__in=[request.user, other_user]
    ).order_by('timestamp')

    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = other_user
            msg.save()
            return redirect('exams:view_message', user_id=other_user.id)
    else:
        form = MessageForm()

    return render(request, 'messaging/view_message.html', {
        'other_user': other_user,
        'messages': messages,
        'form': form,
    })
@staff_member_required
def bulk_upload_questions(request, exam_id):
    exam = CourseExam.objects.get(id=exam_id)

    if request.method == 'POST':
        form = BulkQuestionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file, engine='openpyxl')
                else:
                    form.add_error('file', 'Unsupported file type. Please upload CSV or Excel (.xlsx).')
                    return render(request, 'bulk_upload.html', {'form': form, 'exam': exam})

                # Clean and validate each row
                for _, row in df.iterrows():
                    if pd.isnull(row['text']) or pd.isnull(row['correct_option']):
                        continue  # skip invalid rows
                    CourseQuestion.objects.create(
                        exam=exam,
                        text=row['text'],
                        option_a=row['option_a'],
                        option_b=row['option_b'],
                        option_c=row['option_c'],
                        option_d=row['option_d'],
                        correct_option=str(row['correct_option']).strip().upper()
                    )
                return redirect('exams:exam_detail', exam_id=exam.id)

            except Exception as e:
                form.add_error('file', f"Error processing file: {e}")

    else:
        form = BulkQuestionUploadForm()

    return render(request, 'exams/bulk_upload.html', {'form': form, 'exam': exam})

def exam_detail(request, exam_id):
    exam = get_object_or_404(CourseExam, id=exam_id)
    questions = exam.questions.all()  # Using related_name='questions' from your model

    return render(request, 'courses/exam_detail.html', {
        'exam': exam,
        'questions': questions
    })

def edit_question(request, question_id):
    question = get_object_or_404(CourseQuestion, id=question_id)
    if request.method == 'POST':
        form = CourseQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('exams:exam_detail', exam_id=question.exam.id)
    else:
        form = CourseQuestionForm(instance=question)

    return render(request, 'courses/edit_question.html', {'form': form, 'question': question})

def delete_question(request, question_id):
    question = get_object_or_404(CourseQuestion, id=question_id)
    exam_id = question.exam.id
    question.delete()
    return redirect('exams:exam_detail', exam_id=exam_id)

@require_POST
@login_required
def enroll_in_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment, created = CourseEnrollment.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, f"You have successfully enrolled in '{course.title}'.")
    else:
        messages.info(request, f"You are already enrolled in '{course.title}'.")
    return redirect('exams:list_courses')

@login_required
def list_courses(request):
    courses = Course.objects.all()
    user_enrollments = CourseEnrollment.objects.filter(user=request.user).values_list('course_id', flat=True)

    return render(request, 'exams/course_list.html', {
        'courses': courses,
        'user_enrollments': user_enrollments,
    })

@login_required
def exam_panel(request):
    enrolled_courses = CourseEnrollment.objects.filter(user=request.user).values_list('course', flat=True)
    exams = CourseExam.objects.filter(course__in=enrolled_courses).select_related('course')

    submissions = ExamSubmission.objects.filter(user=request.user)
    submission_map = {s.exam.id: s for s in submissions}

    # Stats
    total_exams = exams.count()
    taken_exams = submissions.count()
    not_taken = total_exams - taken_exams

    return render(request, 'exams/exam_panel.html', {
        'exams': exams,
        'submission_map': submission_map,
        'total_exams': total_exams,
        'taken_exams': taken_exams,
        'not_taken': not_taken,
    })

# def student_past_questions(request):
#     student = request.user
#     enrolled_courses = CourseEnrollment.objects.filter(user=request.user).values_list('course', flat=True)
#     past_questions = PastQuestionFile.objects.filter(course_id__in=enrolled_courses).order_by('-year')

#     return render(request, 'student/past_questions.html', {
#         'past_questions': past_questions
#     })

@staff_member_required
def upload_past_question(request):
    if request.method == 'POST':
        form = PastQuestionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('exams:past_questions')
    else:
        form = PastQuestionUploadForm()
    return render(request, 'exams/upload_past_question.html', {'form': form})

def past_questions(request):
    q = request.GET.get('q', '')
    course_id = request.GET.get('course')
    year = request.GET.get('year')

    question_files = PastQuestionFile.objects.all()

    if q:
        question_files = question_files.filter(Q(title__icontains=q) | Q(course__name__icontains=q))
    if course_id:
        question_files = question_files.filter(course__id=course_id)
    if year:
        question_files = question_files.filter(year=year)

    courses = Course.objects.all()
    years = PastQuestionFile.objects.order_by('year').values_list('year', flat=True).distinct()

    return render(request, 'exams/past_questions.html', {
        'question_files': question_files,
        'courses': courses,
        'years': years,
    })

@staff_member_required
def custom_admin_dashboard(request):
    # Submissions per exam, using 'name' instead of 'title'
    submissions_per_exam = CourseExamAttempt.objects.values('exam__name').annotate(total=Count('id'))

    # Average scores over time, using completed_at
    seven_days_ago = timezone.now() - timedelta(days=7)
    avg_scores = (
        CourseExamAttempt.objects.filter(completed_at__gte=seven_days_ago)
        .extra({'day': "date(completed_at)"})
        .values('day')
        .annotate(avg_score=Avg('score'))
        .order_by('day')
    )

    # Dynamic stats for dashboard cards
    total_users = User.objects.count()
    submissions_today = CourseExamAttempt.objects.filter(
        started_at__date=timezone.now().date()
    ).count()
    # Assuming 'pending_reviews' means incomplete attempts (completed_at is null)
    pending_reviews = CourseExamAttempt.objects.filter(completed_at__isnull=True).count()

    # Data for dynamic URLs
    exams = CourseExam.objects.all()
    courses = Course.objects.all()
    questions = CourseQuestion.objects.all()

    # Context for template
    context = {
        'submissions_per_exam': list(submissions_per_exam),
        'avg_scores': list(avg_scores),
        'total_users': total_users,
        'submissions_today': submissions_today,
        'pending_reviews': pending_reviews,
        'exams': exams,
        'courses': courses,
        'questions': questions,
    }

    return render(request, 'admin_dashboard/dashboard_home.html', context)

@login_required
def download_result_pdf(request, exam_id):
    from xhtml2pdf import pisa
    exam = get_object_or_404(CourseExam, id=exam_id)
    submission = get_object_or_404(ExamSubmission, exam=exam, user=request.user)

    template = get_template('exams/result_pdf.html')
    html = template.render({'submission': submission})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Result_{exam.name}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response

@login_required
def leaderboard(request, exam_id):
    exam = get_object_or_404(CourseExam, id=exam_id)
    submissions = ExamSubmission.objects.filter(exam=exam).order_by('-score')[:50]

    context = {
        'exam': exam,
        'submissions': submissions,
    }
    return render(request, 'exams/leaderboard.html', context)
def export_leaderboard_pdf(request):
    from xhtml2pdf import pisa
    attempts = CourseExamAttempt.objects.select_related('user', 'exam').order_by('-score')
    template_path = 'exams/leaderboard_pdf.html'
    context = {'attempts': attempts}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="leaderboard.pdf"'
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response

def export_course_attempts_excel(request):
    import openpyxl
    from django.http import HttpResponse

    try:
        attempts = CourseExamAttempt.objects.select_related('user', 'exam')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Exam Attempts"
        ws.append(['Student', 'Exam', 'Score', 'Completed At'])  # Updated header

        for attempt in attempts:
            ws.append([
                attempt.user.username if attempt.user else 'N/A',
                attempt.exam.name if attempt.exam else 'N/A',  # Use exam.name (model has name, not title)
                attempt.score if attempt.score is not None else 'N/A',
                attempt.completed_at.strftime('%Y-%m-%d %H:%M') if attempt.completed_at else 'N/A'  # Use completed_at
            ])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=course_exam_attempts.xlsx'
        wb.save(response)
        return response
    except Exception as e:
        return HttpResponse(f"Error generating Excel file: {str(e)}", status=500)