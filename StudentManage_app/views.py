# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, logout as django_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
from collections import defaultdict
from django.db.models import Count, Q, Sum
import json
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import hashlib
from functools import wraps
from .forms import StudentForm, DepartmentForm, SubjectForm, SubjectSelectForm
from .models import (Student, Department, Teacher, Fee, Attendance, Result, Subject,AttendanceSession, TeacherSubject)
import time



# TEACHER AUTHENTICATION ("""Helper to get current teacher from session""")
def get_current_teacher(request):
    teacher_id = request.session.get('teacher_id')
    if teacher_id:
        try:
            return Teacher.objects.get(id=teacher_id, status=True)
        except Teacher.DoesNotExist:
            if 'teacher_id' in request.session:
                del request.session['teacher_id']
    return None


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
@teacher_login_required
def attendance_dashboard(request):
    """Main attendance dashboard — STRICT teacher-only access"""
    teacher = request.teacher  # Set by decorator
    
    today = timezone.now().date()
    
    my_sessions_today = AttendanceSession.objects.filter(
        teacher=teacher, date=today
    ).count()
    
    my_total_sessions = AttendanceSession.objects.filter(teacher=teacher).count()
    
    recent_sessions = AttendanceSession.objects.filter(
        teacher=teacher
    ).select_related('subject').order_by('-date', '-start_time')[:10]
    
    total_students = Student.objects.count()
    today_records = Attendance.objects.filter(session__date=today)
    present_today = today_records.filter(status='Present').count()
    absent_today = today_records.filter(status='Absent').count()
    
    # Department stats (last 7 days)
    last_7_days = today - timezone.timedelta(days=7)
    dept_stats = []
    for dept in Department.objects.all():
        total = Attendance.objects.filter(
            session__date__gte=last_7_days,
            student__department=dept
        ).count()
        present = Attendance.objects.filter(
            session__date__gte=last_7_days,
            student__department=dept,
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
        'recent_sessions': recent_sessions,
        'dept_stats': dept_stats,
    }
    
    # CRITICAL: Must return the render response
    return render(request, 'StudentManage_app/attendance/dashboard.html', context)

@teacher_login_required
def session_create(request):
    teacher = get_current_teacher(request)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        period = request.POST.get('period')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time') or '09:00'
        end_time = request.POST.get('end_time') or '10:00'
        
        if not date:
            messages.error(request, "Date is required.")
            return redirect('session_create')
        if not subject_id:
            messages.error(request, "Subject is required.")
            return redirect('session_create')
        if not period:
            messages.error(request, "Period is required.")
            return redirect('session_create')
        
        if AttendanceSession.objects.filter(subject_id=subject_id, teacher=teacher, date=date, period=period).exists():
            messages.error(request, "A session already exists for this subject, date and period.")
            return redirect('session_create')
        
        session = AttendanceSession.objects.create(
            subject_id=subject_id,
            teacher=teacher,
            date=date,
            period=period,
            start_time=start_time,
            end_time=end_time
        )
        messages.success(request, "Attendance session created successfully!")
        return redirect('take_attendance', session_id=session.id)
    
    subjects = Subject.objects.all()
    context = {'subjects': subjects, 'teacher': teacher}
    return render(request, 'StudentManage_app/attendance/session_form.html', context)

@teacher_login_required
def session_list(request):
    """List all attendance sessions for the logged-in teacher"""
    teacher = request.teacher
    
    # Get all sessions for this teacher, newest first
    sessions = AttendanceSession.objects.filter(
        teacher=teacher
    ).select_related('subject').order_by('-date', '-start_time')
    
    # Stats
    total_sessions = sessions.count()
    today_sessions = sessions.filter(date=timezone.now().date()).count()
    
    return render(request, 'StudentManage_app/attendance/session_list.html', {
        'teacher': teacher,
        'sessions': sessions,
        'total_sessions': total_sessions,
        'today_sessions': today_sessions,
    })
# views.py
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
    session = get_object_or_404(AttendanceSession, id=session_id)
    teacher = get_current_teacher(request)
    
    if session.teacher != teacher and not teacher.is_teacher_admin:
        messages.error(request, "You can only take attendance for your own sessions.")
        return redirect('session_list')
    
    if session.is_completed:
        messages.warning(request, "This session is already completed.")
        return redirect('session_detail', session_id=session.id)
    
    students = Student.objects.filter(
        department=session.subject.department,
        year=session.subject.year
    ).order_by('roll_no')
    
    if request.method == 'POST':
        present_count = 0
        absent_count = 0
        
        with transaction.atomic():
            for student in students:
                status = request.POST.get(f'student_{student.id}', 'Absent')
                remark = request.POST.get(f'remark_{student.id}', '')
                
                Attendance.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={'status': status, 'remarks': remark}
                )
                
                if status == 'Present':
                    present_count += 1
                else:
                    absent_count += 1
            
            session.is_completed = True
            session.total_students = students.count()
            session.present_count = present_count
            session.absent_count = absent_count
            session.save()
        
        messages.success(request, f"Attendance saved! Present: {present_count}, Absent: {absent_count}")
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
def session_detail(request, session_id):
    session = get_object_or_404(AttendanceSession.objects.select_related('subject', 'teacher'), id=session_id)
    teacher = get_current_teacher(request)
    
    if session.teacher != teacher and not teacher.is_teacher_admin:
        messages.error(request, "You can only view your own sessions.")
        return redirect('session_list')
    
    records = session.records.select_related('student').order_by('student__roll_no')
    
    total = records.count()
    present = records.filter(status='Present').count()
    absent = records.filter(status='Absent').count()
    late = records.filter(status='Late').count()
    
    context = {
        'session': session,
        'records': records,
        'teacher': teacher,
        'stats': {
            'total': total,
            'present': present,
            'absent': absent,
            'late': late,
            'percentage': round((present / total * 100), 1) if total else 0
        }
    }
    return render(request, 'StudentManage_app/attendance/session_detail.html', context)


@teacher_login_required
def attendance_report(request):
    teacher = get_current_teacher(request)
    records = Attendance.objects.select_related('student', 'session', 'session__subject').filter(session__teacher=teacher).order_by('-session__date')
    
    subject_id = request.GET.get('subject')
    student_id = request.GET.get('student')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    
    if subject_id:
        records = records.filter(session__subject_id=subject_id)
    if student_id:
        records = records.filter(student_id=student_id)
    if date_from:
        records = records.filter(session__date__gte=date_from)
    if date_to:
        records = records.filter(session__date__lte=date_to)
    if status:
        records = records.filter(status=status)
    
    subjects = Subject.objects.all()
    students = Student.objects.all()
    
    context = {
        'records': records,
        'subjects': subjects,
        'students': students,
        'total_records': records.count(),
        'teacher': teacher,
    }
    return render(request, 'StudentManage_app/attendance/attendance_report.html', context)


@teacher_login_required
def student_attendance_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    teacher = get_current_teacher(request)
    
    attendances = student.attendances.select_related('session', 'session__subject').filter(session__teacher=teacher).order_by('-session__date')
    
    total = attendances.count()
    present = attendances.filter(status='Present').count()
    absent = attendances.filter(status='Absent').count()
    late = attendances.filter(status='Late').count()
    
    subject_stats = []
    subjects = Subject.objects.filter(department=student.department, year=student.year)
    for subject in subjects:
        sub_total = attendances.filter(session__subject=subject).count()
        sub_present = attendances.filter(session__subject=subject, status='Present').count()
        sub_percentage = (sub_present / sub_total * 100) if sub_total > 0 else 0
        subject_stats.append({
            'name': subject.subject_name,
            'total': sub_total,
            'present': sub_present,
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
            'percentage': round((present / total * 100), 1) if total else 0
        },
        'subject_stats': subject_stats,
    }
    return render(request, 'StudentManage_app/attendance/student_detail.html', context)


@teacher_login_required
def edit_attendance(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    teacher = get_current_teacher(request)
    
    if session.teacher != teacher and not teacher.is_teacher_admin:
        messages.error(request, "You can only edit your own sessions.")
        return redirect('session_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            for record in session.records.all():
                new_status = request.POST.get(f'student_{record.student.id}', record.status)
                new_remark = request.POST.get(f'remark_{record.student.id}', record.remarks or '')
                record.status = new_status
                record.remarks = new_remark
                record.save()
            
            session.present_count = session.records.filter(status='Present').count()
            session.absent_count = session.records.filter(status='Absent').count()
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


@teacher_login_required
def low_attendance_report(request):
    teacher = get_current_teacher(request)
    threshold = 75
    
    students = Student.objects.filter(department__subjects__sessions__teacher=teacher).distinct()
    low_attendance_students = []
    
    for student in students:
        total = student.attendances.filter(session__teacher=teacher).count()
        if total == 0:
            continue
        present = student.attendances.filter(session__teacher=teacher, status='Present').count()
        percentage = (present / total) * 100
        
        if percentage < threshold:
            low_attendance_students.append({
                'student': student,
                'total': total,
                'present': present,
                'percentage': round(percentage, 1)
            })
    
    low_attendance_students.sort(key=lambda x: x['percentage'])
    
    context = {
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