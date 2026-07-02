# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, logout as django_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
from collections import defaultdict
from django.db.models import Count, Q, Sum, Case, When, FloatField, F
import json
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import hashlib
from functools import wraps
from .forms import StudentForm, DepartmentForm, SubjectForm, SubjectSelectForm
from .models import (Student, Department, Teacher, Fee, Attendance, Result, Subject,AttendanceSession, TeacherSubject)
import time
from collections import defaultdict
import qrcode
import qrcode.image.svg
from io import BytesIO
from django.http import HttpResponse
from django.urls import reverse
from .forms import (
    AttendanceSessionForm, 
    AttendanceFilterForm, 
    LowAttendanceFilterForm, 
    QRCheckinForm
)
from .models import AttendanceSession, Attendance, Subject, Student, Department, Teacher
# from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache


 
def custom_logout(request):
    logout(request)
    request.session.flush()
    return redirect('/accounts/login/')

"""Decorator to check if teacher is logged in — WORKING VERSION"""
def teacher_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        teacher_id = request.session.get('teacher_id')
        
        if not teacher_id:
            messages.error(request, "Please login as teacher to access this page.")
            return redirect('teacher_login')
        
        # Verify teacher still exists and is active
        try:
            teacher = Teacher.objects.get(id=teacher_id, status=True)
            request.teacher = teacher 
        except Teacher.DoesNotExist:
            if 'teacher_id' in request.session:
                del request.session['teacher_id']
            messages.error(request, "Session expired. Please login again.")
            return redirect('teacher_login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper



# TEACHER LOGIN / LOGOUT("""Independent teacher login page""")

def teacher_login(request):    
    # If already logged in as teacher, redirect to dashboard
    if request.session.get('teacher_id'):
        return redirect('attendance_dashboard')
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id', '').strip()
        password = request.POST.get('password', '')
        
        if not teacher_id or not password:
            messages.error(request, 'Both Teacher ID and Password are required.')
            return render(request, 'StudentManage_app/attendance/teacher_login.html')
        
        try:
            teacher = Teacher.objects.get(teacher_id=teacher_id, status=True)
            
            if teacher.check_password(password):
                # CRITICAL: Set session and mark as modified
                request.session['teacher_id'] = teacher.id
                request.session.modified = True  # Forces Django to save the session without even anything changed
                request.session.set_expiry(3600)  # 1 hour, will automatically logout after it
                
                messages.success(request, f'Welcome, {teacher.name}!')
                return redirect('attendance_dashboard')
            else:
                # Anti-brute force: small delay
                time.sleep(0.5)
                messages.error(request, 'Invalid password. Please try again.')
                
        except Teacher.DoesNotExist:
            # Same delay for non-existent users (timing attack prevention)
            time.sleep(0.5)
            messages.error(request, 'Teacher ID not found.')
    
    return render(request, 'StudentManage_app/attendance/teacher_login.html')



"""Logout teacher — completely clear ALL sessions"""
def teacher_logout(request):
    #(Clear teacher-specific session keys first and using pop() cuz morre safer than del
    for key in ['teacher_id', 'teacher_name', 'teacher_id_display']:
        request.session.pop(key, None)  
   
    django_logout(request) # (this also calls flush() internally)
    request.session.flush()#flush the session for extra safety
    
    messages.success(request, "You have been logged out successfully.")
    return redirect('teacher_login')

# ============================================================
# ADMIN DASHBOARD (Django Auth)
# ============================================================
 
@login_required
def dashboard(request):
    students = Student.objects.select_related('department').all()
    total_students = students.count()
    recent_students = students.order_by('-created_at')[:5]
    departments = Department.objects.annotate(
        student_count=Count('students', distinct=True),
        subject_count=Count('subjects', distinct=True),
    ).order_by('-student_count', 'name')[:5]
    year_summary = students.values('year').annotate(count=Count('id')).order_by('year')
    department_summary = Department.objects.annotate(
        student_count=Count('students')
    ).order_by('name')
    monthly_summary = students.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(count=Count('id')).order_by('month')

    monthly_labels = [item['month'].strftime('%b') for item in monthly_summary if item['month']]
    monthly_data = [item['count'] for item in monthly_summary if item['month']]
    department_labels = [department.name for department in department_summary]
    department_student_data = [department.student_count for department in department_summary]

    context = {
        'total_students': total_students,
        'total_departments': Department.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_fees': Fee.objects.count(),
        'total_attendance': Attendance.objects.count(),
        'total_results': Result.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_users': User.objects.count(),
        'total_classes': Student.objects.values('department').distinct().count(),
        'departments': departments,
        'year_summary': year_summary,
        'monthly_labels': json.dumps(monthly_labels or ['No Data']),
        'monthly_data': json.dumps(monthly_data or [0]),
        'department_labels': json.dumps(department_labels or ['No Data']),
        'department_student_data': json.dumps(department_student_data or [0]),
        'recent_students': recent_students
    }
    return render(request, 'dashboard.html', context)

# ============================================================
# STUDENT CRUD (Admin)
# ============================================================
#  
@login_required
def student_list(request):
    students = Student.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    year = request.GET.get('year')
    if query:
        students = students.filter(Q(name__icontains=query) | Q(roll_no__icontains=query) | Q(department__name__icontains=query))
    if year:
        students = students.filter(year=year)
    paginator = Paginator(students, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'query': query,
        'year': year,
    }
    return render(request, 'StudentManage_app/list.html', context)

 
@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()
    context = {'form': form}
    return render(request, 'StudentManage_app/add.html', context)

 
@login_required
def student_detail(request, id):
    student = get_object_or_404(Student, id=id)
    context = {'student': student}
    return render(request, 'StudentManage_app/detail.html', context)

 
@login_required
def edit_student(request, id):
    student = get_object_or_404(Student, id=id)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    context = {'form': form, 'student': student}
    return render(request, 'StudentManage_app/edit.html', context)

 
@login_required
def delete_student(request, id):
    student = get_object_or_404(Student, id=id)
    student.delete()
    return redirect('student_list')


# ============================================================
# DEPARTMENT CRUD (Admin)
# ============================================================

    
@login_required
def department_list(request):
    departments = Department.objects.select_related('hod').all()
    hod_count = departments.filter(hod__isnull=False).count()
    return render(request, 'StudentManage_app/departments.html', {
        'departments': departments,
        'hod_count': hod_count
    })


 
@login_required
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm()
    context = {'form': form}
    return render(request, 'StudentManage_app/add_department.html', context)

 
@login_required
def department_detail(request, id):
    department = get_object_or_404(Department, id=id)
    context = {'department': department}
    return render(request, 'StudentManage_app/department_detail.html', context)

 
@login_required
def edit_department(request, id):
    department = get_object_or_404(Department, id=id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    context = {'form': form, 'department': department}
    return render(request, 'StudentManage_app/edit_department.html', context)

 
@login_required
def delete_department(request, id):
    department = get_object_or_404(Department, id=id)
    department.delete()
    return redirect('department_list')


# ============================================================
# SUBJECT CRUD (Admin)
# ============================================================
 
@login_required
def subject_list(request):
    departments = Department.objects.annotate(
        subject_count=Count('subjects'),
        total_credits=Sum('subjects__credits'),
    ).order_by('name')
    context = {'departments': departments}
    return render(request, 'StudentManage_app/sub/subject_list.html', context)

 
@login_required
def subject_select(request):
    """Select an existing subject"""
    if request.method == 'POST':
        form = SubjectSelectForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            return redirect('subject_detail', id=subject.id)
    else:
        form = SubjectSelectForm()
    
    return render(request, 'StudentManage_app/sub/subject_select.html', {
        'form': form,
        'subjects': Subject.objects.all().order_by('subject_name')
    })



 
@login_required
def subject_department_list(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    subjects = Subject.objects.filter(department=department).order_by('year', 'semester', 'subject_name')
    grouped_subjects = defaultdict(list)
    for subject in subjects:
        key = (subject.year, subject.semester)
        grouped_subjects[key].append(subject)
    grouped_data = []
    for key, subjects in grouped_subjects.items():
        total_credits = sum(subject.credits for subject in subjects)
        grouped_data.append({
            'year': key[0],
            'semester': key[1],
            'subjects': subjects,
            'total_credits': float(total_credits),
        })
    context = {
        'department': department,
        'grouped_data': grouped_data,
    }
    return render(request, 'StudentManage_app/sub/subject_department_list.html', context)



 
@login_required
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'StudentManage_app/sub/subject_form.html', {'form': form})


@login_required
def subject_detail(request, id):
    subject = get_object_or_404(Subject, id=id)
    return render(request, 'StudentManage_app/sub/subject_detail.html', {'subject': subject})



 
@login_required
def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'StudentManage_app/sub/subject_form.html', {'form': form})



 
@login_required
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request, 'StudentManage_app/sub/subject_confirm_delete.html', {'subject': subject})


# ============================================================
# TEACHER CRUD (Admin)
# ============================================================
 
@login_required
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, "StudentManage_app/tech/teachers.html", {"teachers": teachers})


 
@login_required
def add_teacher(request):
    departments = Department.objects.all()
    
    if request.method == "POST":
        teacher_id = request.POST.get('teacher_id', '').strip()
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        department_id = request.POST.get('department')
        qualification = request.POST.get('qualification', '').strip()
        experience = request.POST.get('experience', 0)
        joining_date = request.POST.get('joining_date') or None
        password = request.POST.get('password', '')
        is_admin = request.POST.get('is_teacher_admin') == 'on'
        
        errors = []
        if not teacher_id:
            errors.append("Teacher ID is required.")
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if not phone:
            errors.append("Phone is required.")
        if not department_id:
            errors.append("Department is required.")
        if not password:
            errors.append("Password is required.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        
        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            errors.append("Teacher ID already exists.")
        if Teacher.objects.filter(email=email).exists():
            errors.append("Email already exists.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'StudentManage_app/tech/add_teacher.html', {
                'departments': departments
            })
        
        try:
            department = Department.objects.get(id=department_id)
            new_teacher = Teacher.objects.create(
                teacher_id=teacher_id,
                name=name,
                email=email,
                phone=phone,
                department=department,
                qualification=qualification,
                experience=int(experience) if experience else 0,
                joining_date=joining_date,
                status=True,
                is_teacher_admin=is_admin
            )
            new_teacher.set_password(password)
            new_teacher.save()
            
            messages.success(request, f"Teacher '{name}' created! Login ID: {teacher_id}")
            return redirect('teacher_list')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return render(request, 'StudentManage_app/tech/add_teacher.html', {
        'departments': departments
    })


 
@login_required
def teacher_detail(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    context = {
        'teacher': teacher,
        'department': teacher.headed_departments.first()
    }
    return render(request, 'StudentManage_app/tech/teacher_detail.html', context)



 
@login_required
def edit_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    if request.method == "POST":
        teacher.name = request.POST.get('name', teacher.name)
        teacher.email = request.POST.get('email', teacher.email)
        teacher.phone = request.POST.get('phone', teacher.phone)
        teacher.save()
        return redirect('teacher_list')
    return render(request, 'StudentManage_app/tech/edit_teacher.html', {'teacher': teacher})



 
@login_required
def delete_teacher(request, id):
    teacher = get_object_or_404(Teacher, id=id)
    teacher.delete()
    return redirect('teacher_list')


# ============================================================
# ATTENDANCE (Teacher Portal)
# ============================================================


# TEACHER AUTHENTICATION ("""Helper to get current teacher from session""")
def get_teacher(request):
    teacher_id = request.session.get('teacher_id')
    if teacher_id:
        try:
            return Teacher.objects.get(id=teacher_id, status=True)
        except Teacher.DoesNotExist:
            if 'teacher_id' in request.session:
                del request.session['teacher_id']
    return None


@teacher_login_required
def attendance_dashboard(request):
    """Modern attendance dashboard with analytics"""
    teacher = get_teacher(request)
    today = timezone.now().date()
    
    # Teacher's stats
    my_sessions_today = AttendanceSession.objects.filter(
        teacher=teacher, date=today
    ).count()
    
    my_total_sessions = AttendanceSession.objects.filter(teacher=teacher).count()
    
    recent_sessions = AttendanceSession.objects.filter(
        teacher=teacher
    ).select_related('subject').order_by('-date', '-start_time')[:10]
    
    # Global stats
    total_students = Student.objects.count()
    today_records = Attendance.objects.filter(session__date=today)
    present_today = today_records.filter(status='Present').count()
    absent_today = today_records.filter(status='Absent').count()
    late_today = today_records.filter(status='Late').count()
    
    # Department stats (last 7 days) — FIXED: use correct reverse relation
    last_7_days = today - timezone.timedelta(days=7)
    
    dept_stats = []
    for dept in Department.objects.all():
        # Get all students in this department
        dept_student_ids = Student.objects.filter(department=dept).values_list('id', flat=True)
        
        # Count attendance for these students in last 7 days
        total = Attendance.objects.filter(
            session__date__gte=last_7_days,
            student_id__in=dept_student_ids
        ).count()
        
        present = Attendance.objects.filter(
            session__date__gte=last_7_days,
            student_id__in=dept_student_ids,
            status='Present'
        ).count()
        
        percentage = (present / total * 100) if total > 0 else 0
        
        dept_stats.append({
            'name': dept.name,
            'total': total,
            'present': present,
            'percentage': round(percentage, 1)
        })
    
    context = {
        'teacher': teacher,
        'my_sessions_today': my_sessions_today,
        'my_total_sessions': my_total_sessions,
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'recent_sessions': recent_sessions,
        'dept_stats': dept_stats,
    }
    
    return render(request, 'StudentManage_app/attendance/dashboard.html', context)


@teacher_login_required
def session_create(request):
    """Create new attendance session with grouped subjects"""
    from collections import defaultdict
    teacher = get_teacher(request)
    
    if request.method == 'POST':
        form = AttendanceSessionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if AttendanceSession.objects.filter(
                subject=data['subject'], teacher=teacher, 
                date=data['date'], period=data['period']
            ).exists():
                messages.error(request, "A session already exists for this subject, date and period.")
                return redirect('session_create')
            
            session = form.save(commit=False)
            session.teacher = teacher
            session.status = 'scheduled'
            session.save()
            
            messages.success(request, "Attendance session created successfully!")
            return redirect('take_attendance', session_id=session.id)
    else:
        form = AttendanceSessionForm()
    
    # Group subjects for template - CONVERT ALL TO REGULAR DICTS
    subjects_grouped = {}
    for subject in Subject.objects.select_related('department').order_by('department__name', 'year', 'semester', 'subject_name'):
        dept_name = subject.department.name
        year_sem = f"{subject.get_year_display()}, {subject.get_semester_display()}"
        
        if dept_name not in subjects_grouped:
            subjects_grouped[dept_name] = {}
        if year_sem not in subjects_grouped[dept_name]:
            subjects_grouped[dept_name][year_sem] = []
        
        subjects_grouped[dept_name][year_sem].append(subject)
    
    context = {
        'form': form,
        'teacher': teacher,
        'subjects_grouped': subjects_grouped,
    }
    return render(request, 'StudentManage_app/attendance/session_form.html', context)


@teacher_login_required
def session_list(request):
    """List all sessions with filtering"""
    teacher = get_teacher(request)
    
    sessions = AttendanceSession.objects.filter(
        teacher=teacher
    ).select_related('subject').annotate(
        attendance_rate=Case(
            When(total_students__gt=0, then=F('present_count') * 100.0 / F('total_students')),
            default=0,
            output_field=FloatField()
        )
    ).order_by('-date', '-start_time')
    
    # Filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    subject_id = request.GET.get('subject')
    status_filter = request.GET.get('status')
    
    if date_from:
        sessions = sessions.filter(date__gte=date_from)
    if date_to:
        sessions = sessions.filter(date__lte=date_to)
    if subject_id:
        sessions = sessions.filter(subject_id=subject_id)
    if status_filter:
        sessions = sessions.filter(status=status_filter)
    
    # Stats
    total_sessions = sessions.count()
    today_sessions = sessions.filter(date=timezone.now().date()).count()
    completed_sessions = sessions.filter(is_completed=True).count()
    
    subjects = Subject.objects.all()
    
    return render(request, 'StudentManage_app/attendance/session_list.html', {
        'teacher': teacher,
        'sessions': sessions,
        'subjects': subjects,
        'total_sessions': total_sessions,
        'today_sessions': today_sessions,
        'completed_sessions': completed_sessions,
    })


@teacher_login_required
def session_detail(request, session_id):
    """Session detail with full analytics"""
    session = get_object_or_404(
        AttendanceSession.objects.select_related('subject', 'teacher'), 
        id=session_id
    )
    teacher = get_teacher(request)
    
    if session.teacher != teacher and not teacher.is_teacher_admin:
        messages.error(request, "You can only view your own sessions.")
        return redirect('session_list')
    
    records = session.records.select_related('student').order_by('student__roll_no')
    
    # Stats — FIXED: all four counts
    total = records.count()
    present = records.filter(status='Present').count()
    absent = records.filter(status='Absent').count()
    late = records.filter(status='Late').count()
    excused = records.filter(status='Excused').count()
    
    # Check-in methods breakdown
    qr_checkins = records.filter(checkin_method='qr_scan').count()
    manual_checkins = records.filter(checkin_method='manual').count()
    
    context = {
        'session': session,
        'records': records,
        'teacher': teacher,
        'stats': {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'percentage': round((present / total * 100), 1) if total else 0,
            'qr_checkins': qr_checkins,
            'manual_checkins': manual_checkins,
        }
    }
    return render(request, 'StudentManage_app/attendance/session_detail.html', context)

# ============ ATTENDANCE TAKING ============
@teacher_login_required
def attendance_sessions(request):
    """List all attendance sessions for the logged-in teacher"""
    teacher = request.teacher
    sessions = AttendanceSession.objects.filter(teacher=teacher).order_by('-date', '-start_time')
    return render(request, 'StudentManage_app/attendance/sessions.html', {
        'teacher': teacher,
        'sessions': sessions,
    })

@teacher_login_required
def take_attendance(request, session_id):
    """Take attendance — manual or prepare for QR"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    teacher = get_teacher(request)
    
    if session.teacher != teacher and not teacher.is_teacher_admin:
        messages.error(request, "You can only take attendance for your own sessions.")
        return redirect('session_list')
    
    if session.is_completed:
        messages.warning(request, "This session is already completed.")
        return redirect('session_detail', session_id=session.id)
    
    # Get eligible students
    students = Student.objects.filter(
        department=session.subject.department,
        year=session.subject.year
    ).order_by('roll_no')
    
    if request.method == 'POST':
        present_count = absent_count = late_count = excused_count = 0
        
        with transaction.atomic():
            for student in students:
                status = request.POST.get(f'student_{student.id}', 'Absent')
                remark = request.POST.get(f'remark_{student.id}', '')
                
                Attendance.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={
                        'status': status, 
                        'remarks': remark,
                        'marked_by': teacher,
                        'checkin_method': 'manual'
                    }
                )
                
                # FIXED: Proper counting for all statuses
                if status == 'Present':
                    present_count += 1
                elif status == 'Absent':
                    absent_count += 1
                elif status == 'Late':
                    late_count += 1
                elif status == 'Excused':
                    excused_count += 1
            
            session.is_completed = True
            session.status = 'completed'
            session.total_students = students.count()
            session.present_count = present_count
            session.absent_count = absent_count
            session.late_count = late_count
            session.excused_count = excused_count
            session.save()
        
        messages.success(
            request, 
            f"Attendance saved! Present: {present_count}, Absent: {absent_count}, "
            f"Late: {late_count}, Excused: {excused_count}"
        )
        return redirect('session_detail', session_id=session.id)
    
    existing_records = {rec.student_id: rec for rec in session.records.all()}
    
    context = {
        'session': session,
        'students': students,
        'existing_records': existing_records,
        'status_choices': Attendance.STATUS_CHOICES,
        'teacher': teacher,
    }
    return render(request, 'StudentManage_app/attendance/take_attendance.html', context)


@teacher_login_required
def edit_attendance(request, session_id):
    """Edit attendance records"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    teacher = get_teacher(request)
    
    if session.teacher != teacher and not teacher.is_teacher_admin:
        messages.error(request, "You can only edit your own sessions.")
        return redirect('session_list')
    
    if request.method == 'POST':
        present_count = absent_count = late_count = excused_count = 0
        
        with transaction.atomic():
            for record in session.records.all():
                new_status = request.POST.get(f'student_{record.student.id}', record.status)
                new_remark = request.POST.get(f'remark_{record.student.id}', record.remarks or '')
                
                record.status = new_status
                record.remarks = new_remark
                record.marked_by = teacher
                record.save()
                
                # FIXED: Proper counting
                if new_status == 'Present':
                    present_count += 1
                elif new_status == 'Absent':
                    absent_count += 1
                elif new_status == 'Late':
                    late_count += 1
                elif new_status == 'Excused':
                    excused_count += 1
            
            session.present_count = present_count
            session.absent_count = absent_count
            session.late_count = late_count
            session.excused_count = excused_count
            session.save()
        
        messages.success(request, "Attendance updated successfully!")
        return redirect('session_detail', session_id=session.id)
    
    records = session.records.select_related('student').order_by('student__roll_no')
    context = {
        'session': session,
        'records': records,
        'status_choices': Attendance.STATUS_CHOICES,
        'teacher': teacher,
    }
    return render(request, 'StudentManage_app/attendance/edit_attendance.html', context)

# ============ QR CODE SYSTEM ============(new added)


@teacher_login_required
def generate_qr(request, session_id):
    """Generate QR code for student self check-in"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    teacher = get_teacher(request)
    
    if session.teacher != teacher:
        messages.error(request, "You can only generate QR for your own sessions.")
        return redirect('session_list')
    
    if session.is_completed:
        messages.warning(request, "Cannot generate QR for completed session.")
        return redirect('session_detail', session_id=session.id)
    
    # Generate/refresh QR
    session.regenerate_qr(minutes_valid=15)
    session.status = 'ongoing'
    session.save(update_fields=['status'])
    
    # Build QR URL
    qr_url = request.build_absolute_uri(
        reverse('qr_checkin', kwargs={'qr_uuid': session.qr_uuid})
    )
    
    # Generate QR image as SVG
    qr_svg = None
    try:
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        
        print("=" * 50)
        print("Generating QR for URL:", qr_url)
        
        factory = qrcode.image.svg.SvgImage
        qr = qrcode.make(qr_url, image_factory=factory)
        buffer = BytesIO()
        qr.save(buffer)
        qr_svg = buffer.getvalue().decode('utf-8')
        
        print("QR SVG LENGTH:", len(qr_svg))
        print("QR SVG START:", qr_svg[:200])
        print("=" * 50)
        
    except Exception as e:
        print("QR GENERATION ERROR:", str(e))
        import traceback
        traceback.print_exc()
    
    messages.success(request, f"QR Code generated! Valid for 15 minutes.")
    
    context = {
        'session': session,
        'qr_svg': qr_svg,
        'qr_url': qr_url,
        'expires_at': session.qr_expires_at,
        'is_valid': session.is_qr_valid,
    }
    return render(request, 'StudentManage_app/attendance/qr_display.html', context)

@teacher_login_required
def qr_display(request, session_id):
    """Display QR code for students to scan"""
    session = get_object_or_404(AttendanceSession, id=session_id)
    teacher = get_teacher(request)
    
    if session.teacher != teacher:
        messages.error(request, "Access denied.")
        return redirect('session_list')
    
    qr_url = request.build_absolute_uri(
        reverse('qr_checkin', kwargs={'qr_uuid': session.qr_uuid})
    )
    
    # Generate SVG QR
    factory = qrcode.image.svg.SvgImage
    qr = qrcode.make(qr_url, image_factory=factory)
    buffer = BytesIO()
    qr.save(buffer)
    qr_svg = buffer.getvalue().decode('utf-8')
    
    context = {
        'session': session,
        'qr_svg': qr_svg,
        'qr_url': qr_url,
        'expires_at': session.qr_expires_at,
        'is_valid': session.is_qr_valid,
    }
    return render(request, 'StudentManage_app/attendance/qr_display.html', context)

def qr_checkin(request, qr_uuid):
    """Student self check-in via QR code scan using form"""
    session = get_object_or_404(AttendanceSession, qr_uuid=qr_uuid)
    
    if not session.is_qr_valid:
        messages.error(request, "This QR code has expired.")
        return redirect('teacher_login')
    
    if session.is_completed:
        messages.error(request, "This session has already been completed.")
        return redirect('teacher_login')
    
    form = QRCheckinForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        roll_no = form.cleaned_data['roll_no']
        student_name = form.cleaned_data['student_name']
        
        try:
            student = Student.objects.get(roll_no=roll_no, name__iexact=student_name)
            
            # Verify eligibility
            if not Student.objects.filter(
                id=student.id,
                department=session.subject.department,
                year=session.subject.year
            ).exists():
                messages.error(request, "You are not eligible for this session.")
                return redirect('qr_checkin', qr_uuid=qr_uuid)
            
            attendance, created = Attendance.objects.get_or_create(
                session=session,
                student=student,
                defaults={
                    'status': 'Present',
                    'checkin_method': 'qr_scan',
                    'checked_in_at': timezone.now()
                }
            )
            
            if not created:
                messages.warning(request, "Your attendance was already recorded.")
            else:
                messages.success(request, f"Attendance marked as Present!")
            
            return redirect('qr_success', attendance_id=attendance.id)
            
        except Student.DoesNotExist:
            messages.error(request, "Invalid roll number or name.")
    
    context = {
        'form': form,
        'session': session,
        'subject': session.subject,
        'expires_in': int((session.qr_expires_at - timezone.now()).total_seconds() / 60),
    }
    return render(request, 'StudentManage_app/attendance/qr_checkin.html', context)

def qr_success(request, attendance_id):
    """Success page after QR check-in"""
    attendance = get_object_or_404(
        Attendance.objects.select_related('session', 'session__subject', 'student'),
        id=attendance_id
    )
    return render(request, 'StudentManage_app/attendance/qr_success.html', {
        'attendance': attendance
    })


# ============ REPORTS ============

@teacher_login_required
def attendance_report(request):
    """Advanced attendance report with filter form"""
    teacher = get_teacher(request)
    
    # Initialize form with GET data
    form = AttendanceFilterForm(request.GET or None)
    
    records = Attendance.objects.select_related(
        'student', 'session', 'session__subject'
    ).filter(session__teacher=teacher).order_by('-session__date')
    
    # Apply filters from form
    if form.is_valid():
        data = form.cleaned_data
        if data.get('subject'):
            records = records.filter(session__subject=data['subject'])
        if data.get('student'):
            records = records.filter(student=data['student'])
        if data.get('date_from'):
            records = records.filter(session__date__gte=data['date_from'])
        if data.get('date_to'):
            records = records.filter(session__date__lte=data['date_to'])
        if data.get('status'):
            records = records.filter(status=data['status'])
        if data.get('checkin_method'):
            records = records.filter(checkin_method=data['checkin_method'])
    
    # Summary stats
    total_records = records.count()
    present_count = records.filter(status='Present').count()
    qr_count = records.filter(checkin_method='qr_scan').count()
    
    context = {
        'form': form,
        'records': records,
        'total_records': total_records,
        'present_count': present_count,
        'qr_adoption': round((qr_count / total_records * 100), 1) if total_records else 0,
        'teacher': teacher,
    }
    return render(request, 'StudentManage_app/attendance/attendance_report.html', context)

@teacher_login_required
def student_attendance_detail(request, student_id):
    """Individual student attendance analytics"""
    student = get_object_or_404(Student, id=student_id)
    teacher = get_teacher(request)
    
    attendances = student.attendances.select_related(
        'session', 'session__subject'
    ).filter(session__teacher=teacher).order_by('-session__date')
    
    total = attendances.count()
    present = attendances.filter(status='Present').count()
    absent = attendances.filter(status='Absent').count()
    late = attendances.filter(status='Late').count()
    excused = attendances.filter(status='Excused').count()
    
    # Subject-wise breakdown
    subject_stats = []
    subjects = Subject.objects.filter(department=student.department, year=student.year)
    
    for subject in subjects:
        sub_total = attendances.filter(session__subject=subject).count()
        sub_present = attendances.filter(session__subject=subject, status='Present').count()
        sub_late = attendances.filter(session__subject=subject, status='Late').count()
        sub_percentage = (sub_present / sub_total * 100) if sub_total > 0 else 0
        
        subject_stats.append({
            'name': subject.subject_name,
            'total': sub_total,
            'present': sub_present,
            'late': sub_late,
            'percentage': round(sub_percentage, 1)
        })
    
    context = {
        'student': student,
        'attendances': attendances,
        'teacher': teacher,
        'stats': {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'excused': excused,
            'percentage': round((present / total * 100), 1) if total else 0
        },
        'subject_stats': subject_stats,
    }
    return render(request, 'StudentManage_app/attendance/student_detail.html', context)



@teacher_login_required
def low_attendance_report(request):
    """Low attendance report with threshold form"""
    teacher = get_teacher(request)
    
    form = LowAttendanceFilterForm(request.GET or None)
    threshold = 75
    
    if form.is_valid():
        threshold = form.cleaned_data.get('threshold', 75)
    
    # OPTIMIZED: Using annotations instead of N+1 queries
    students = Student.objects.filter(
        attendances__session__teacher=teacher
    ).annotate(
        total=Count('attendances'),
        present=Count('attendances', filter=Q(attendances__status='Present')),
        absent=Count('attendances', filter=Q(attendances__status='Absent')),
        late=Count('attendances', filter=Q(attendances__status='Late'))
    ).annotate(
        percentage=Case(
            When(total__gt=0, then=F('present') * 100.0 / F('total')),
            default=0,
            output_field=FloatField()
        )
    ).filter(percentage__lt=threshold).order_by('percentage')[:50]
    
    # Build the list for template
    low_attendance_students = [
        {
            'student': student,
            'total': student.total,
            'present': student.present,
            'absent': student.absent,
            'late': student.late,
            'percentage': round(student.percentage, 1)
        }
        for student in students
    ]
    
    context = {
        'form': form,
        'students': low_attendance_students,
        'threshold': threshold,
        'teacher': teacher,
    }
    return render(request, 'StudentManage_app/attendance/low_attendance.html', context)
# ============================================================
# RESULTS & FEES
# ============================================================

def result_list(request):
    results = Result.objects.all()
    return render(request, 'StudentManage_app/results.html', {'results': results})


def fee_list(request):
    fees = Fee.objects.all()
    return render(request, 'StudentManage_app/fees.html', {'fees': fees})


def user_list(request):
    users = User.objects.all()
    return render(request, 'StudentManage_app/users.html', {'users': users})


def profile(request):
    return render(request, 'StudentManage_app/profile.html')