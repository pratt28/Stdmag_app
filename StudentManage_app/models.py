from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import settings

# department model
class Department(models.Model):
    name = models.CharField(max_length=100)
    hod = models.CharField(max_length=100)
    
    @property
    def total_students(self):
        return self.students.count()

    def __str__(self):
        return self.name

#SUBJECT MODEL
#subject CRUD model  
class Subject(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                 related_name='subjects', null=True, blank=True )
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
    semester = models.CharField(max_length=20,choices=SEMESTER_CHOICES,null=True, blank=True)
    year = models.CharField(max_length=20,choices=YEAR_CHOICES,null=True, blank=True)
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20,unique=True)
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
    department = models.ForeignKey(Department,on_delete=models.CASCADE,related_name='students')
    year = models.CharField(max_length=20,choices=YEAR_CHOICES)
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES
    )
    dob = models.DateField()
    address = models.TextField()
    photo = models.ImageField(upload_to='students/',blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-name']
    def __str__(self):
        return self.name
    



 
#teacher model
class Teacher(models.Model):
    
    name = models.CharField(max_length=100)

    email = models.EmailField()

    phone = models.CharField(max_length=15)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
    
#attendance model
class Attendance(models.Model):
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=[
            ('Present','Present'),
            ('Absent','Absent')
        ]
    )

    def __str__(self):
        return self.student.name
    
#result model
class Result(models.Model):
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    subject = models.CharField(max_length=100)

    marks = models.IntegerField()

    grade = models.CharField(max_length=5)

    def __str__(self):
        return self.student.name
    
#fee model
class Fee(models.Model):
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    paid = models.BooleanField(
        default=False
    )

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.student.name
