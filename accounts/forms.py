# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control gradient-input',
            'placeholder': 'Enter username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control gradient-input',
            'placeholder': 'Enter password'
        })
    )

# accounts/forms.py
class UserRegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Do not expose the 'superadmin' role in the public user creation form
        if 'role' in self.fields:
            self.fields['role'].choices = [
                choice for choice in self.fields['role'].choices
                if choice[0] != 'superadmin'
            ]

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control gradient-input',
            'placeholder': 'Enter password'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control gradient-input',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Last Name'}),
            'role': forms.Select(attrs={'class': 'form-control gradient-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Phone Number'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user