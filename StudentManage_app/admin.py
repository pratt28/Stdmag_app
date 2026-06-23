from django.contrib import admin
from .models import Student,Department,Subject
from .models import Teacher,Fee,Attendance,Result
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'roll_no',
        'department',
        'year',
        'email'
    )
    search_fields = (
        'name',
        'roll_no',
        'department'
    )
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'subject_code', 'department')
from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'teacher_id',
        'name',
        'email',
        'department',
        'status'
    )
    search_fields = (
        'name',
        'email'
    )
    list_filter = (
        'department',
        'status'
    )
admin.site.register(Department)
admin.site.register(Fee)
admin.site.register(Attendance)
admin.site.register(Result)
# Register your models here.
