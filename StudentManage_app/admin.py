from django.contrib import admin
from .models import (Student,Department,Subject,Teacher,Attendance,AttendanceSession,Result,Fee)
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
    list_display = [
        'subject', 'teacher', 'date', 'period', 
        'status', 'is_completed', 'attendance_percentage'
    ]
    list_filter = ['status', 'date', 'is_completed', 'subject__department']
    search_fields = ['subject__subject_name', 'teacher__name', 'period']
    readonly_fields = [
        'qr_uuid', 'qr_enabled', 'qr_expires_at',
        'created_at', 'updated_at', 'attendance_percentage'
    ]
    
    fieldsets = (
        ('Session Info', {
            'fields': ('subject', 'teacher', 'date', 'period', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('status', 'is_completed')
        }),
        ('Attendance Counts', {
            'fields': ('total_students', 'present_count', 'absent_count', 'late_count', 'excused_count')
        }),
        ('QR Code', {
            'fields': ('qr_uuid', 'qr_enabled', 'qr_expires_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'session', 'status', 
        'checkin_method', 'checked_in_at', 'marked_by'
    ]
    list_filter = ['status', 'checkin_method', 'session__date']
    search_fields = ['student__name', 'student__roll_no', 'session__subject__subject_name']
    readonly_fields = ['checked_in_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('session', 'student', 'status', 'remarks')
        }),
        ('Audit Trail', {
            'fields': ('checkin_method', 'checked_in_at', 'marked_by')
        }),
    )

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'marks', 'grade']


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_type', 'amount', 'paid']
    list_filter = ['fee_type', 'paid']