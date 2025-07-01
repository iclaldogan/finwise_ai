from django.contrib import admin
from .models import LoanType, Loan, LoanPayment, LoanEligibility


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_amount', 'max_amount', 'min_term_months', 'max_term_months', 'base_interest_rate']
    list_filter = ['base_interest_rate']
    search_fields = ['name', 'description']
    list_editable = ['base_interest_rate']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Amount Limits', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Term Limits', {
            'fields': ('min_term_months', 'max_term_months')
        }),
        ('Interest Rate', {
            'fields': ('base_interest_rate',)
        }),
    )


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['user', 'loan_type', 'amount', 'interest_rate', 'term_months', 'monthly_payment', 'status', 'is_simulation']
    list_filter = ['status', 'is_simulation', 'loan_type', 'start_date']
    search_fields = ['user__email']
    list_editable = ['status']
    date_hierarchy = 'start_date'
    raw_id_fields = ['user']
    autocomplete_fields = ['loan_type']
    
    fieldsets = (
        ('User & Type', {
            'fields': ('user', 'loan_type', 'is_simulation')
        }),
        ('Loan Terms', {
            'fields': ('amount', 'interest_rate', 'term_months', 'monthly_payment')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status & Balance', {
            'fields': ('status', 'remaining_balance')
        }),
    )


@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'payment_date', 'amount', 'principal_amount', 'interest_amount', 'remaining_balance', 'is_paid']
    list_filter = ['is_paid', 'payment_date']
    search_fields = ['loan__user__email']
    list_editable = ['is_paid']
    date_hierarchy = 'payment_date'
    raw_id_fields = ['loan']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('loan', 'payment_date', 'amount', 'is_paid')
        }),
        ('Breakdown', {
            'fields': ('principal_amount', 'interest_amount', 'remaining_balance')
        }),
    )


@admin.register(LoanEligibility)
class LoanEligibilityAdmin(admin.ModelAdmin):
    list_display = ['user', 'loan_type', 'requested_amount', 'is_eligible', 'max_eligible_amount', 'offered_interest_rate', 'created_at']
    list_filter = ['is_eligible', 'loan_type', 'created_at']
    search_fields = ['user__email', 'reason']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']
    autocomplete_fields = ['loan_type']
    
    fieldsets = (
        ('Request', {
            'fields': ('user', 'loan_type', 'requested_amount', 'requested_term_months')
        }),
        ('Decision', {
            'fields': ('is_eligible', 'max_eligible_amount', 'offered_interest_rate', 'reason')
        }),
    ) 