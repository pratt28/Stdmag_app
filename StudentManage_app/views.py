from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import TruncMonth
from collections import defaultdict# to group students by department
from django.db.models import Count, Sum
import json

from .models import Student,Department,Teacher,Fee,Attendance,Result,Subject
from .forms import StudentForm,DepartmentForm,SubjectForm

# dashboard view
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
    # 'total_profiles': User.objects.filter(profile__isnull=False).count(),
    'recent_students': recent_students
}
    return render(request,'dashboard.html',context)

#STUDENTS
# student CRUD views
def student_list(request):
    students = Student.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    year = request.GET.get('year')
    if query:
        students = students.filter(Q(name__icontains=query) | Q(roll_no__icontains=query) | Q(department__name__icontains=query))
    if year:
        students = students.filter(year=year)
    paginator = Paginator(students,6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'query': query,
        'year': year,
    }
    return render(request,'StudentManage_app/list.html',context)


def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()
    context = {
        'form': form
    }
    return render(request,'StudentManage_app/add.html',context)

def student_detail(request, id):
    student = get_object_or_404(Student,id=id)
    context = {
        'student': student
    }
    return render( request,'StudentManage_app/detail.html',context)

def edit_student(request, id):
    student = get_object_or_404(Student,id=id)
    if request.method == 'POST':
        form = StudentForm(request.POST,request.FILES,instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)

    context = {
        'form': form,
        'student': student
    }
    return render(request,'StudentManage_app/edit.html',context)

def delete_student(request, id):
    student = get_object_or_404(Student,id=id)
    student.delete()
    return redirect('student_list')



# DEPARTMENTS
#department CRUD views

def department_list(request):
    departments = Department.objects.all()
    return render(request,'StudentManage_app/departments.html',{'departments': departments})


def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm()
    context = {
        'form': form
    }
    return render(request,'StudentManage_app/add_department.html', context)
    
    
def department_detail(request, id):
    department = get_object_or_404(Department, id=id)
    context = {
        'department': department
    }
    return render(request,'StudentManage_app/department_detail.html',context
                  )
def edit_department(request, id):
    department = get_object_or_404(Department, id=id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)

        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    context = {
        'form': form,
        'department': department
    }
    return render(request,'StudentManage_app/edit_department.html',context)
    
def delete_department(request, id):
    department = get_object_or_404(Department, id=id)
    department.delete()
    return redirect('department_list')

#SUBJECTS
# subject CRUD views
def subject_list(request):
    departments = Department.objects.annotate(
        subject_count=Count('subjects'),
        total_credits=Sum('subjects__credits'),
    ).order_by('name')

    context = {
        'departments': departments,
    }
    return render(request,'StudentManage_app/sub/subject_list.html',context)


def subject_department_list(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    subjects = Subject.objects.filter(department=department).order_by('year','semester','subject_name')
    grouped_subjects = defaultdict(list)
    for subject in subjects:
        key = (
            subject.year,
            subject.semester
        )   
        
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
    return render(request,'StudentManage_app/sub/subject_department_list.html',context)


def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request,'StudentManage_app/sub/subject_form.html',{'form': form})

def subject_detail(request, id):
    subject = get_object_or_404(Subject, id=id)
    return render(request,'StudentManage_app/sub/subject_detail.html',{'subject': subject})


def subject_update(request, pk):
    
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request,'StudentManage_app/sub/subject_form.html',{'form': form})

def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request,'StudentManage_app/sub/subject_confirm_delete.html',{'subject': subject})
# =====================
# TEACHERS
# ======================

def teacher_list(request):

    teachers = Teacher.objects.all()

    return render(
        request,
        'StudentManage_app/teachers.html',
        {'teachers': teachers}
    )


# ======================
# ATTENDANCE
# ======================

def attendance_list(request):

    attendance = Attendance.objects.all()

    return render(
        request,
        'StudentManage_app/attendance.html',
        {'attendance': attendance}
    )


# ======================
# RESULTS
# ======================

def result_list(request):

    results = Result.objects.all()

    return render(
        request,
        'StudentManage_app/results.html',
        {'results': results}
    )


# ======================
# FEES
# ======================

def fee_list(request):

    fees = Fee.objects.all()

    return render(
        request,
        'StudentManage_app/fees.html',
        {'fees': fees}
    )
    
def user_list(request):
    users = User.objects.all()

    context = {
        'users': users
    }

    return render(request, 'StudentManage_app/users.html', context)

def profile(request):
    return render(request, 'StudentManage_app/profile.html')


# Create your views here.
