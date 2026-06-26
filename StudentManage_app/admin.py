from django.contrib import admin
from .models import (Student,Department,Subject,Teacher,Attendance,AttendanceSession,Result,Fee)

# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display = (
#         'name',
#         'roll_no',
#         'department',
#         'year',
#         'email'
#     )
#     search_fields = (
#         'name',
#         'roll_no',
#         'department'
#     )
# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('subject_name', 'subject_code', 'department')
# from django.contrib import admin
# from .models import Teacher


# @admin.register(Teacher)
# class TeacherAdmin(admin.ModelAdmin):
#     list_display = (
#         'teacher_id',
#         'name',
#         'email',
#         'department',
#         'status'
#     )
#     search_fields = (
#         'name',
#         'email'
#     )
#     list_filter = (
#         'department',
#         'status'
#     )
# @admin.register(AttendanceSession)
# class AttendanceSessionAdmin(admin.ModelAdmin):
#     list_display = ['subject', 'teacher', 'date', 'period', 'is_completed', 'present_count', 'absent_count']
#     list_filter = ['date', 'is_completed', 'subject__department']
#     search_fields = ['subject__subject_name', 'teacher__name']
#     date_hierarchy = 'date'

# @admin.register(Attendance)
# class AttendanceAdmin(admin.ModelAdmin):
#     list_display = ['student', 'session', 'status', 'marked_by', 'created_at']
#     list_filter = ['status', 'session__date', 'session__subject']
#     search_fields = ['student__name', 'student__roll_no']
#     list_editable = ['status']

# @admin.register(Department)
# class DepartmentAdmin(admin.ModelAdmin):
#     list_display = ['name', 'hod', 'total_students']
    

# @admin.register(Result)
# class ResultAdmin(admin.ModelAdmin):
#     list_display = ['student', 'subject', 'marks', 'grade']

# @admin.register(Fee)
# class FeeAdmin(admin.ModelAdmin):
#     list_display = ['student', 'fee_type', 'amount', 'paid', 'due_date']
#     list_filter = ['paid', 'fee_type']





# @admin.register(AttendanceSession)
# class AttendanceSessionAdmin(admin.ModelAdmin):
#     list_display = ['subject', 'teacher', 'date', 'period', 'is_completed', 'present_count', 'absent_count']
#     list_filter = ['date', 'is_completed', 'subject__department']
#     search_fields = ['subject__subject_name', 'teacher__name']
#     date_hierarchy = 'date'

# @admin.register(Attendance)
# class AttendanceAdmin(admin.ModelAdmin):
#     list_display = ['student', 'session', 'status', 'remarks']  # Removed 'marked_by' and 'created_at'
#     list_filter = ['status', 'session__date', 'session__subject']
#     search_fields = ['student__name', 'student__roll_no']
#     list_editable = ['status']

# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display = ['roll_no', 'name', 'department', 'year', 'email', 'phone']
#     list_filter = ['department', 'year', 'gender']
#     search_fields = ['name', 'roll_no', 'email']

# @admin.register(Teacher)
# class TeacherAdmin(admin.ModelAdmin):
#     list_display = ['teacher_id', 'name', 'department', 'email', 'status']
#     list_filter = ['department', 'status']
#     search_fields = ['name', 'teacher_id', 'email']

# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ['subject_code', 'subject_name', 'department', 'year', 'semester', 'credits']
#     list_filter = ['department', 'year', 'semester']
#     search_fields = ['subject_name', 'subject_code']

# @admin.register(Department)
# class DepartmentAdmin(admin.ModelAdmin):
#     list_display = ['name', 'hod', 'total_students']

# @admin.register(Result)
# class ResultAdmin(admin.ModelAdmin):
#     list_display = ['student', 'subject', 'marks', 'grade']

# @admin.register(Fee)
# class FeeAdmin(admin.ModelAdmin):
#     list_display = ['student', 'fee_type', 'amount', 'paid', 'due_date']
#     list_filter = ['paid', 'fee_type']

# # Register your models here.



from django.contrib import admin
from django import forms
from .models import Teacher, Department, Student, Subject, AttendanceSession, Attendance, Result, Fee


class TeacherAdminForm(forms.ModelForm):
    """Form with password field that gets hashed on save"""
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Enter password to set/change it. Leave blank to keep existing."
    )
    
    class Meta:
        model = Teacher
        fields = '__all__'
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            teacher.set_password(password)
        if commit:
            teacher.save()
        return teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ['teacher_id', 'name', 'email', 'department', 'is_teacher_admin', 'status']
    list_filter = ['department', 'is_teacher_admin', 'status']
    search_fields = ['teacher_id', 'name', 'email']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('teacher_id', 'name', 'email', 'phone')
        }),
        ('Professional', {
            'fields': ('qualification', 'experience', 'department', 'joining_date')
        }),
        ('Authentication', {
            'fields': ('password',),  # Shows password input instead of hash
            'description': 'Enter password to set/change. Will be hashed automatically.'
        }),
        ('Permissions', {
            'fields': ('is_teacher_admin', 'status')
        }),
        ('System', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']


# Register other models
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'hod_name', 'total_students']
    
    def hod_name(self, obj):
        return obj.hod.name if obj.hod else "—"
    hod_name.short_description = "HOD"



@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_no', 'name', 'department', 'year', 'email']
    list_filter = ['department', 'year', 'gender']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_code', 'subject_name', 'department', 'year', 'semester', 'credits']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'teacher', 'date', 'period', 'is_completed']
    list_filter = ['date', 'is_completed']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'session', 'status']
    list_filter = ['status']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'marks', 'grade']


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_type', 'amount', 'paid']
    list_filter = ['fee_type', 'paid']