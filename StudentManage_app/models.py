# from django.db import models
# from django.utils import timezone
# from django.contrib.auth.models import User
# from django.contrib.auth import settings
# from django.core.exceptions import ValidationError

# # department model
# class Department(models.Model):
#     name = models.CharField(max_length=100)
#     hod = models.CharField(max_length=100)
    
#     @property
#     def total_students(self):
#         return self.students.count()

#     def __str__(self):
#         return self.name

# #SUBJECT MODEL
# #subject CRUD model  
# class Subject(models.Model):
#     department = models.ForeignKey(Department, on_delete=models.CASCADE,
#                  related_name='subjects', null=True, blank=True )
#     YEAR_CHOICES = (
#         ('1st Year', '1st Year'),
#         ('2nd Year', '2nd Year'),
#         ('3rd Year', '3rd Year'),
#         ('4th Year', '4th Year'),
#     )
#     SEMESTER_CHOICES = (
#         ('1st Semester', '1st Semester'),
#         ('2nd Semester', '2nd Semester'),
#         ('3rd Semester', '3rd Semester'),
#         ('4th Semester', '4th Semester'),
#         ('5th Semester', '5th Semester'),
#         ('6th Semester', '6th Semester'),
#         ('7th Semester', '7th Semester'),
#         ('8th Semester', '8th Semester'),
#     )
#     semester = models.CharField(max_length=20,choices=SEMESTER_CHOICES,null=True, blank=True)
#     year = models.CharField(max_length=20,choices=YEAR_CHOICES,null=True, blank=True)
#     subject_name = models.CharField(max_length=100)
#     subject_code = models.CharField(max_length=20,unique=True)
#     credits = models.IntegerField(default=3)

#     def __str__(self):
#         return f"{self.subject_name} ({self.department.name})"
    
# class Student(models.Model):
#     YEAR_CHOICES = (
#         ('1st Year', '1st Year'),
#         ('2nd Year', '2nd Year'),
#         ('3rd Year', '3rd Year'),
#         ('4th Year', '4th Year'),
#     )
#     GENDER_CHOICES = (
#         ('Male', 'Male'),
#         ('Female', 'Female'),
#         ('Other', 'Other'),
#     )
#     name = models.CharField(max_length=100)
#     roll_no = models.CharField(max_length=20, unique=True)
#     email = models.EmailField(unique=True)
#     phone = models.CharField(max_length=15)
#     department = models.ForeignKey(Department,on_delete=models.CASCADE,related_name='students')
#     year = models.CharField(max_length=20,choices=YEAR_CHOICES)
#     gender = models.CharField(
#         max_length=20,
#         choices=GENDER_CHOICES
#     )
#     dob = models.DateField()
#     address = models.TextField()
#     photo = models.ImageField(upload_to='students/',blank=True,null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         ordering = ['-name']
#     def __str__(self):
#         return self.name
 
# #teacher model
# class Teacher(models.Model):
#     user=models.OneToOneField(User,on_delete=models.CASCADE,null=True,blank=True)
#     teacher_id = models.CharField(max_length=20,null=True,unique=True)
#     name = models.CharField(max_length=100)
#     email = models.EmailField(unique=True)
#     phone = models.CharField(max_length=15)
#     qualification = models.CharField(max_length=100,null=True,blank=True)
#     experience = models.IntegerField( default=0)
#     department = models.ForeignKey(Department,on_delete=models.CASCADE)
#     joining_date = models.DateField(null=True,blank=True)
#     status = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     def __str__(self):
#         return self.name
    
# #attendance model
# # class Attendance(models.Model):
# #     STATUS_CHOICES = [
# #         ('Present', 'Present'),
# #         ('Absent', 'Absent'),
# #         ('Late', 'Late'),           # Added: common real-world status
# #         ('Excused', 'Excused'),      # Added: medical leave, etc.
# #         ('On Duty', 'On Duty'),      # Added: representing college, etc.
# #     ]

# #     student = models.ForeignKey(Student,on_delete=models.CASCADE,related_name='attendances')
# #     subject = models.ForeignKey(Subject,on_delete=models.CASCADE,related_name='attendances',null=True, blank=True)
# #     teacher = models.ForeignKey(Teacher,on_delete=models.SET_NULL,  # Keep record even if teacher leaves
# #         null=True,
# #         related_name='attendances_taken'
# #     )

# #     date = models.DateField(default=timezone.now)
# #     time = models.TimeField(default=timezone.now)
    
# #     # Optional: track which period/session
# #     period = models.CharField(max_length=50, blank=True, null=True)  
# #     status = models.CharField(
# #         max_length=10,
# #         choices=STATUS_CHOICES,
# #         default='Present'
# #     )
    
# #     remarks = models.TextField(blank=True, null=True)  # Reason for absence/late
# #     created_at = models.DateTimeField(auto_now_add=True)
# #     updated_at = models.DateTimeField(auto_now=True)

# #     class Meta:
# #         # CRITICAL: Prevent duplicate attendance for same student+subject+date+period
# #         constraints = [
# #             models.UniqueConstraint(
# #                 fields=['student', 'subject', 'date', 'period'],
# #                 name='unique_attendance_per_period'
# #             )
# #         ]
# #         ordering = ['-date', '-time']
# #         indexes = [
# #             models.Index(fields=['student', 'date']),
# #             models.Index(fields=['subject', 'date']),
# #         ]

# #     def clean(self):
# #         # Additional validation: can't mark future attendance
# #         if self.date > timezone.now().date():
# #             raise ValidationError("Cannot mark attendance for future dates.")
        
# #         # Student must belong to the subject's department (optional but good)
# #         if self.subject and self.student.department != self.subject.department:
# #             raise ValidationError("Student does not belong to this subject's department.")

# #     def __str__(self):
# #         return f"{self.student.name} - {self.status} on {self.date}"

# #     def __str__(self):
# #         return self.student.name
    
    
#     class AttendanceSession(models.Model):
#         """A single class/session where attendance is taken"""
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE,related_name='sessions')
#     teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE,related_name='sessions_taken')
#     date = models.DateField(default=timezone.now)
#     period = models.CharField(max_length=50)
#     start_time = models.TimeField()
#     end_time = models.TimeField()
    
#     is_completed = models.BooleanField(default=False)
#     total_students = models.IntegerField(default=0)
#     present_count = models.IntegerField(default=0)
#     absent_count = models.IntegerField(default=0)
    
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ['subject', 'teacher', 'date', 'period']

#     def __str__(self):
#         return f"{self.subject} - {self.date} ({self.period})"


# class Attendance(models.Model):
#     STATUS_CHOICES = [
#         ('Present', 'Present'),
#         ('Absent', 'Absent'),
#         ('Late', 'Late'),
#         ('Excused', 'Excused'),
#     ]
#     session = models.ForeignKey(
#         AttendanceSession,
#         on_delete=models.CASCADE,
#         related_name='records'
#     )
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES)
#     remarks = models.TextField(blank=True, null=True)
    
#     class Meta:
#         unique_together = ['session', 'student']  
#     def __str__(self):
#         return f"{self.student.name}-{self.status}"
    
# #result model
# class Result(models.Model):
    
#     student = models.ForeignKey(
#         Student,
#         on_delete=models.CASCADE
#     )

#     subject = models.CharField(max_length=100)

#     marks = models.IntegerField()

#     grade = models.CharField(max_length=5)
#     exam_date = models.DateField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)


#     class Meta:
#         unique_together = ['student', 'subject']

#     def _str_(self):
#         return f"{self.student.name} - {self.subject.subject_name}"
    
    
# #fee model
# class Fee(models.Model):
#     FEE_TYPES = (
#         ('Tuition', 'Tuition'),
#         ('Exam', 'Exam'),
#         ('Library', 'Library'),
#         ('Lab', 'Lab'),
#         ('Other', 'Other'),
#     )
    
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
#     fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default='Tuition')
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     paid = models.BooleanField(default=False)
#     payment_date = models.DateField(null=True, blank=True)
#     due_date = models.DateField(null=True, blank=True)

#     def _str_(self):
#         return f"{self.student.name} - {self.fee_type}"

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import hashlib
class Department(models.Model):
    name = models.CharField(max_length=100)
    hod = models.ForeignKey(
        'Teacher',  # Use string reference to avoid circular import
        on_delete=models.SET_NULL,  # Keep department if teacher is deleted
        null=True,
        blank=True,
        related_name='headed_departments'  # Access from Teacher side
    )
    
    @property
    def total_students(self):
        return self.students.count()

    def __str__(self):
        return self.name
    
    
    @property
    def hod_name(self):
        """Get HOD name safely"""
        return self.hod.name if self.hod else "Not Assigned"


class Subject(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)
    YEAR_CHOICES = (
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    )
    SEMESTER_CHOICES = (
        ('1st Semester', '1st Semester'),
        ('2nd Semester', '2nd Semester'),
        ('3rd Semester', '3rd Semester'),
        ('4th Semester', '4th Semester'),
        ('5th Semester', '5th Semester'),
        ('6th Semester', '6th Semester'),
        ('7th Semester', '7th Semester'),
        ('8th Semester', '8th Semester'),
    )
    semester = models.CharField(max_length=20, choices=SEMESTER_CHOICES, null=True, blank=True)
    year = models.CharField(max_length=20, choices=YEAR_CHOICES, null=True, blank=True)
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    credits = models.IntegerField(default=3)

    def __str__(self):
        return f"{self.subject_name} ({self.department.name})"


class Student(models.Model):
    YEAR_CHOICES = (
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
    )
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='students')
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    dob = models.DateField()
    address = models.TextField()
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    
    class Meta:
        ordering = ['-name']
    
    def __str__(self):
        return self.name


class Teacher(models.Model):
    """Teacher model with independent login (NOT linked to Django admin)"""
    teacher_id = models.CharField(max_length=20, unique=True,null=True,blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    qualification = models.CharField(max_length=100, null=True, blank=True)
    experience = models.IntegerField(default=0)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    joining_date = models.DateField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)
    
    # 🔐 Independent login credentials (NOT Django auth)
    password_hash = models.CharField(max_length=128, blank=True, null=True)
    is_teacher_admin = models.BooleanField(default=False, help_text="Can manage other teachers")
    
    def set_password(self, raw_password):
        """Hash and store password"""
        import hashlib
        self.password_hash = hashlib.sha256(raw_password.encode()).hexdigest()
    
    def check_password(self, raw_password):
        """Verify password"""
        import hashlib
        return self.password_hash == hashlib.sha256(raw_password.encode()).hexdigest()
    
    def __str__(self):
        return self.name

class AttendanceSession(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='sessions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='sessions_taken')
    date = models.DateField(default=timezone.now)
    period = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_completed = models.BooleanField(default=False)
    total_students = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True,blank=True)

    class Meta:
        unique_together = ['subject', 'teacher', 'date', 'period']

    def __str__(self):
        return f"{self.subject} - {self.date} ({self.period})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records',null=True,blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['session', 'student']

    def __str__(self):
        return f"{self.student.name} - {self.status}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results')
    marks = models.IntegerField()
    grade = models.CharField(max_length=5)
    exam_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'subject']

    def __str__(self):
        return f"{self.student.name} - {self.subject.subject_name}"


class Fee(models.Model):
    FEE_TYPES = (
        ('Tuition', 'Tuition'),
        ('Exam', 'Exam'),
        ('Library', 'Library'),
        ('Lab', 'Lab'),
        ('Other', 'Other'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, default='Tuition')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.fee_type}"





class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assigned_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teachers')
    assigned_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['teacher', 'subject']
    
    def __str__(self):
        return f"{self.teacher.name} - {self.subject.subject_name}"