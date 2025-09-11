from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import SalaryAdvanceRequest, Employee


class SignUpForm(UserCreationForm):
    staffid = forms.CharField(
        max_length=150,
        required=True,
        label="Staff ID",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your Staff ID'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your staff email'})
    )

    class Meta:
        model = User
        fields = ['staffid', 'email', 'password1', 'password2']

    def save(self, commit=True):
        # Don’t save immediately, so we can map staffid -> username
        user = super().save(commit=False)
        user.username = self.cleaned_data['staffid']  # store staffid as username
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

#Salary Form
class SalaryAdvanceForm(forms.ModelForm):
    class Meta:
        model = SalaryAdvanceRequest
        fields = ['amount', 'reason']  # staff info will be auto-filled
        widgets = {
            'amount': forms.NumberInput(attrs={'id': 'amount', 'placeholder': 'Enter amount', 'max': '50000', 'required': True}),
            'reason': forms.Textarea(attrs={'id': 'reason', 'placeholder': 'Optional: Enter reason for request'}),
        }


#Add employee form
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'full_name', 'national_id', 'dob',
            'date_joined', 'department', 'job_title', 
            'employment_type', 'salary', 'email', 'phone', 'address'
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
