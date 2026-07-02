from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import hashlib
import uuid #(for generating unique identifires for teachers and students)
from django.db.models import Count, Q, F, Case, When, FloatField #(for calculating attendance percentahges)


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
    subject_code = models.CharField(max_length=20)
    credits = models.IntegerField(default=3)
    
    class Meta:
        # Same code allowed in different departments
        unique_together = ['department', 'subject_code']
        ordering = ['department__name', 'year', 'semester', 'subject_name']

    # def __str__(self):
    #     return f"{self.subject_name} ({self.department.name})"
    def __str__(self):
        dept_name = self.department.name if self.department else "No Dept"
        return f"{self.subject_name} ({dept_name})"


#Student Model with fields for personal information
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


#teacher model with independent login (NOT linked to Django admin)
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
    
    #Independent login credentials (NOT Django auth)
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
    SESSION_STATUS = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='sessions')
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, related_name='sessions_taken')
    date = models.DateField(default=timezone.now)
    period = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Session status tracking
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='scheduled')
    is_completed = models.BooleanField(default=False)
    
    # Counts — FIXED: all four status types now tracked
    total_students = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    excused_count = models.IntegerField(default=0)
    
    # QR Code for self-check-in
    # default=uuid.uuid4,
    qr_uuid = models.UUIDField( blank=True, null=True, unique=True, editable=False)
    qr_enabled = models.BooleanField(default=False)
    qr_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps — FIXED: auto_now_add instead of null
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['subject', 'teacher', 'date', 'period']
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.subject} - {self.date} ({self.period})"
    
    @property
    def attendance_percentage(self):
        if self.total_students == 0:
            return 0
        return round((self.present_count / self.total_students) * 100, 1)
    
    @property
    def is_qr_valid(self):
        if not self.qr_enabled or not self.qr_expires_at:
            return False
        return timezone.now() < self.qr_expires_at
    
    def regenerate_qr(self, minutes_valid=15):
        """Generate new QR code, valid for specified minutes"""
        self.qr_uuid = uuid.uuid4()
        self.qr_enabled = True
        self.qr_expires_at = timezone.now() + timezone.timedelta(minutes=minutes_valid)
        self.save(update_fields=['qr_uuid', 'qr_enabled', 'qr_expires_at'])
    
    def disable_qr(self):
        self.qr_enabled = False
        self.qr_expires_at = None
        self.save(update_fields=['qr_enabled', 'qr_expires_at'])


class Attendance(models.Model):
    CHECKIN_METHODS = [
        ('manual', 'Manual (Teacher)'),
        ('qr_scan', 'QR Code Self Check-in'),
        ('bulk', 'Bulk Import'),
    ]
    
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused'),
    ]
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records', null=True, blank=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    remarks = models.TextField(blank=True, null=True)
    
    # How the attendance was marked
    checkin_method = models.CharField(max_length=20, choices=CHECKIN_METHODS, default='manual')
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    # who will take the attendance
    marked_by = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_marked')
    
    class Meta:
        unique_together = ['session', 'student']
        ordering = ['-session__date', 'student__roll_no']
    
    def __str__(self):
        return f"{self.student.name} - {self.status}"
    
    def mark_present(self, method='manual', teacher=None):
        self.status = 'Present'
        self.checkin_method = method
        self.checked_in_at = timezone.now()
        if teacher:
            self.marked_by = teacher
        self.save()

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='results')
    marks = models.IntegerField()
    grade = models.CharField(max_length=5)
    # exam_date = models.DateField(null=True, blank=True)
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