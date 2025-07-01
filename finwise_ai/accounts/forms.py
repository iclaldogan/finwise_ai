from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class SignUpForm(UserCreationForm):
    """Form for user registration with email verification."""
    
    email = forms.EmailField(
        max_length=254,
        help_text='Required. Enter a valid email address.',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with remember me functionality."""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    remember_me = forms.BooleanField(required=False, initial=False)
    
    class Meta:
        model = User
        fields = ('username', 'password', 'remember_me')


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with styled widgets."""
    
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with styled widgets."""
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'})
    )


class UserProfileForm(forms.ModelForm):
    """Form for user profile information."""
    
    monthly_income = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly Income'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    
    class Meta:
        model = UserProfile
        fields = ('monthly_income', 'preferred_currency', 'risk_profile', 
                  'date_of_birth', 'phone_number', 'savings_focused', 
                  'investment_focused', 'budget_conscious')
        widgets = {
            'preferred_currency': forms.Select(attrs={'class': 'form-select'}),
            'risk_profile': forms.Select(attrs={'class': 'form-select'}),
            'savings_focused': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'investment_focused': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'budget_conscious': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
