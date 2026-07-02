from django import forms
from dal import autocomplete
from .models import Student,Department,Subject,AttendanceSession,Attendance,Teacher

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'  #the auto generated form will include all the fields of the model
        widgets = {
            # in html this looks like <input type="text" class="form-control">
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'roll_no': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date','class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
        }
        
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Department Name'}),
                   'hod': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        # Only show active teachers in the dropdown
            self.fields['hod'].queryset = Teacher.objects.filter(status=True)
            self.fields['hod'].required = False
            self.fields['hod'].empty_label = "— Select HOD —"

    
        
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = '__all__'
        widgets = {
            'subject_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject_code': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
        }
class SubjectSelectForm(forms.Form):
    """Form to select an existing subject from database"""
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all().order_by('subject_name'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="---no subject selected---"
    )        

class AttendanceSessionForm(forms.ModelForm):
    """Form for creating attendance sessions"""
    
    class Meta:
        model = AttendanceSession
        fields = ['subject', 'date', 'period', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Period 1, Morning Session'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Don't render the default subject field - we'll use our custom HTML
        self.fields['subject'].widget = forms.HiddenInput()


class BulkAttendanceForm(forms.Form):
    """Dynamic form for taking bulk attendance"""
    def __init__(self, students, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for student in students:
            self.fields[f'student_{student.id}'] = forms.ChoiceField(
                choices=Attendance.STATUS_CHOICES,
                initial='Present',
                required=True,
                widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
            )
            self.fields[f'remark_{student.id}'] = forms.CharField(
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-control form-control-sm',
                    'placeholder': 'Remark (optional)'
                })
            )




# class AttendanceFilterForm(forms.Form):
#     subject = forms.ModelChoiceField(
#         queryset=Subject.objects.all(),
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )
#     student = forms.ModelChoiceField(
#         queryset=Student.objects.all(),
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )
#     date_from = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )
#     date_to = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
#     )
#     status = forms.ChoiceField(
#         choices=[('', 'All')] + list(Attendance.STATUS_CHOICES),
#         required=False,
#         widget=forms.Select(attrs={'class': 'form-select'})
#     )

class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance reports"""
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All')] + list(Attendance.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    checkin_method = forms.ChoiceField(
        choices=[('', 'All')] + list(Attendance.CHECKIN_METHODS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class QRCheckinForm(forms.Form):
    """Form for student QR code self check-in"""
    roll_no = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your roll number',
            'autofocus': True
        })
    )
    student_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )


class LowAttendanceFilterForm(forms.Form):
    """Form for filtering low attendance report"""
    threshold = forms.IntegerField(
        min_value=0,
        max_value=100,
        initial=75,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Threshold %'
        })
    )