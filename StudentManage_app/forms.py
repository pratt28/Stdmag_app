from django import forms
from .models import Student,Department,Subject

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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'hod': forms.TextInput(attrs={'class': 'form-control'}),
            # 'total_students': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
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