from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

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
