from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import SalaryAdvanceRequest, Employee, Profile, LoanRequest
from django.core.exceptions import ValidationError
from django.db import transaction



# ================================================================
# Sign Up Form
# ================================================================
class SignUpForm(UserCreationForm):
    """
    Custom user signup form.
    - Requires a valid Staff ID and staff email.
    - Verifies that Staff ID and Email correspond to an existing Employee.
    - Creates a User and links it to Employee + Profile atomically.
    """

    staffid = forms.CharField(
        max_length=150,
        required=True,
        label="Staff ID",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your Staff ID'})
    )
    email = forms.EmailField(
        required=True,
        label="Staff Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your staff email'})
    )

    class Meta:
        model = User
        # Note: form template should reference form.staffid and form.email
        fields = ['staffid', 'email', 'password1', 'password2']

    # ---------------- Field-level validation ----------------
    def clean_staffid(self):
        """Ensure Staff ID is unique and exists in Employee records."""
        staffid = (self.cleaned_data.get('staffid') or '').strip()
        if not staffid:
            raise ValidationError("Staff ID is required.")
        if User.objects.filter(username__iexact=staffid).exists():
            raise ValidationError("An account already exists for this Staff ID.")
        if not Employee.objects.filter(staff_id__iexact=staffid).exists():
            raise ValidationError("No employee found with that Staff ID. Contact HR.")
        return staffid

    def clean_email(self):
        """Ensure Email is unique and not reused by another User."""
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        """
        Cross-field validation:
        Confirm that the Staff ID and Email combination matches an Employee record.
        """
        cleaned = super().clean()
        staffid = (cleaned.get('staffid') or '').strip()
        email = (cleaned.get('email') or '').strip().lower()

        if staffid and email:
            if not Employee.objects.filter(staff_id__iexact=staffid, email__iexact=email).exists():
                raise ValidationError("Staff ID and Email do not match our employee records.")
        return cleaned

    # ---------------- Save ----------------
    @transaction.atomic
    def save(self, commit=True):
        """
        Create the User atomically.
        - Copies employee details into the User record.
        - Ensures Profile is created/linked properly.
        """
        staffid = self.cleaned_data['staffid'].strip()
        email = self.cleaned_data['email'].strip().lower()
        password = self.cleaned_data['password1']

        # Create User (triggers post_save signal if configured)
        user = User.objects.create_user(username=staffid, email=email, password=password)

        # Sync names from Employee record
        try:
            employee = Employee.objects.get(staff_id__iexact=staffid)
            name_parts = (employee.full_name or "").strip().split(" ", 1)
            user.first_name = name_parts[0] if len(name_parts) >= 1 else ""
            user.last_name = name_parts[1] if len(name_parts) > 1 else ""
            user.save(update_fields=['first_name', 'last_name'])
        except Employee.DoesNotExist:
            employee = None

        # Create or update Profile
        profile, created = Profile.objects.get_or_create(user=user)
        if employee:
            profile.employee = employee
        profile.role = profile.role or "STAFF"
        profile.save()

        return user


# ================================================================
# Salary Advance Request Form
# ================================================================
class SalaryAdvanceForm(forms.ModelForm):
    """
    Form to handle staff salary advance requests.
    - Amount and reason are filled by the staff member.
    - User info is auto-handled by the view.
    """
    class Meta:
        model = SalaryAdvanceRequest
        fields = ['amount', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'id': 'amount',
                'placeholder': 'Enter amount',
                'max': '50000',
                'required': True
            }),
            'reason': forms.Textarea(attrs={
                'id': 'reason',
                'placeholder': 'Optional: Enter reason for request'
            }),
        }


# ================================================================
# Employee Form
# ================================================================
class EmployeeForm(forms.ModelForm):
    """
    Form for adding/editing Employee records in the system.
    """
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


# ================================================================
# Profile Update Form
# ================================================================
class ProfileUpdateForm(forms.ModelForm):
    """
    Simple form to allow staff to update their profile picture.
    """
    class Meta:
        model = Profile
        fields = ["profile_picture"]


# ================================================================
# Loan Request Form
# ================================================================
class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = LoanRequest
        fields = ['amount', 'repayment_period', 'reason']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'id': 'loanAmount',
                'placeholder': 'Enter loan amount',
                'required': True
            }),
            'repayment_period': forms.Select(attrs={
                'id': 'repaymentPeriod',
                'required': True
            }, choices=[(6, "6 Months"), (12, "12 Months"), (18, "18 Months"), (24, "24 Months")]),
            'reason': forms.Textarea(attrs={
                'id': 'reason',
                'placeholder': 'Optional: Enter reason for request'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop("employee", None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if self.employee:
            max_allowed = self.employee.salary * 2
            if amount > max_allowed:
                raise forms.ValidationError(
                    f"You cannot request more than KES {max_allowed:,.2f}."
                )
        return amount
