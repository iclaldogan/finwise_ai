from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import uuid
import datetime

from .forms import SignUpForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm, UserProfileForm
from .models import User, UserProfile, EmailVerification, PasswordReset


def signup_view(request):
    """Handle user registration with email verification."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True  # User can login but with limited access until email is verified
            user.email_verified = False
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Generate verification token
            token = str(uuid.uuid4())
            expiry = timezone.now() + datetime.timedelta(days=2)  # Token valid for 2 days
            EmailVerification.objects.create(user=user, token=token, expires_at=expiry)
            
            # Send verification email
            subject = 'Verify your FinWise AI account'
            verification_url = request.build_absolute_uri(
                reverse('accounts:verify_email', kwargs={'token': token})
            )
            message = render_to_string('accounts/email/verification_email.html', {
                'user': user,
                'verification_url': verification_url,
                'expiry_days': 2,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)
            
            messages.success(request, 'Account created successfully! Please check your email to verify your account.')
            return redirect('accounts:login')
    else:
        form = SignUpForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def verify_email_view(request, token):
    """Verify user email with token."""
    try:
        verification = EmailVerification.objects.get(token=token)
        
        # Check if token is expired
        if verification.expires_at < timezone.now():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('accounts:login')
        
        # Mark user as verified
        user = verification.user
        user.email_verified = True
        user.save()
        
        # Delete the verification token
        verification.delete()
        
        messages.success(request, 'Email verified successfully! You can now login to your account.')
        return redirect('accounts:login')
    
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:login')


def login_view(request):
    """Handle user login with remember me functionality."""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Set session expiry based on remember me
                if remember_me:
                    # Session will last for 2 weeks
                    request.session.set_expiry(1209600)
                else:
                    # Session will end when browser is closed
                    request.session.set_expiry(0)
                
                # Redirect to dashboard if email is verified, otherwise show warning
                if user.email_verified:
                    return redirect('dashboard')
                else:
                    messages.warning(request, 'Please verify your email to access all features.')
                    return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


def password_reset_request_view(request):
    """Handle password reset request."""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate reset token
                token = str(uuid.uuid4())
                expiry = timezone.now() + datetime.timedelta(hours=24)  # Token valid for 24 hours
                PasswordReset.objects.create(user=user, token=token, expires_at=expiry)
                
                # Send reset email
                subject = 'Reset your FinWise AI password'
                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', kwargs={'token': token})
                )
                message = render_to_string('accounts/email/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'expiry_hours': 24,
                })
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)
                
                messages.success(request, 'Password reset link has been sent to your email.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                messages.success(request, 'Password reset link has been sent to your email if the account exists.')
                return redirect('accounts:login')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, token):
    """Handle password reset confirmation."""
    try:
        reset = PasswordReset.objects.get(token=token)
        
        # Check if token is expired
        if reset.expires_at < timezone.now():
            messages.error(request, 'Password reset link has expired. Please request a new one.')
            return redirect('accounts:password_reset_request')
        
        if request.method == 'POST':
            form = CustomSetPasswordForm(reset.user, request.POST)
            if form.is_valid():
                user = form.save()
                
                # Delete the reset token
                reset.delete()
                
                messages.success(request, 'Password has been reset successfully. You can now login with your new password.')
                return redirect('accounts:login')
        else:
            form = CustomSetPasswordForm(reset.user)
        
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    
    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('accounts:password_reset_request')


@login_required
def profile_view(request):
    """Handle user profile view and update."""
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {'form': form, 'user': user})


@login_required
def resend_verification_email_view(request):
    """Resend verification email if not verified."""
    user = request.user
    
    if user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('dashboard')
    
    # Delete any existing verification tokens
    EmailVerification.objects.filter(user=user).delete()
    
    # Generate new verification token
    token = str(uuid.uuid4())
    expiry = timezone.now() + datetime.timedelta(days=2)  # Token valid for 2 days
    EmailVerification.objects.create(user=user, token=token, expires_at=expiry)
    
    # Send verification email
    subject = 'Verify your FinWise AI account'
    verification_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'token': token})
    )
    message = render_to_string('accounts/email/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
        'expiry_days': 2,
    })
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)
    
    messages.success(request, 'Verification email has been sent. Please check your inbox.')
    return redirect('dashboard')
