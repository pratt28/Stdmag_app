from django import forms
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
        

class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['subject', 'period', 'date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Period 1, Morning Session'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
        }


class BulkAttendanceForm(forms.Form):
    """Form for taking bulk attendance - one checkbox per student"""
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


class AttendanceFilterForm(forms.Form):
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