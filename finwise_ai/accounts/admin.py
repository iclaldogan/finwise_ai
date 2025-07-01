from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile, EmailVerification, PasswordReset


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model with no username field."""
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email_verified')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'email_verified')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    inlines = (UserProfileInline,)


class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    search_fields = ('user__email',)


class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    search_fields = ('user__email',)


admin.site.register(User, UserAdmin)
admin.site.register(EmailVerification, EmailVerificationAdmin)
admin.site.register(PasswordReset, PasswordResetAdmin)
