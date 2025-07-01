from django.contrib import admin
from .models import CreditFactor, CreditHistory, CreditFactorScore, CreditEstimation, ImprovementSuggestion


@admin.register(CreditFactor)
class CreditFactorAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight']
    list_editable = ['weight']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Factor Details', {
            'fields': ('name', 'description', 'weight')
        }),
    )


@admin.register(CreditHistory)
class CreditHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'score', 'date', 'report_source', 'created_at']
    list_filter = ['score', 'date', 'report_source']
    search_fields = ['user__email', 'report_source', 'notes']
    date_hierarchy = 'date'
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'score')
        }),
        ('Details', {
            'fields': ('report_source', 'notes'),
            'classes': ('collapse',),
        }),
    )


@admin.register(CreditFactorScore)
class CreditFactorScoreAdmin(admin.ModelAdmin):
    list_display = ['credit_history', 'factor', 'score']
    list_filter = ['factor', 'score']
    search_fields = ['credit_history__user__email', 'factor__name', 'notes']
    raw_id_fields = ['credit_history']
    autocomplete_fields = ['factor']
    
    fieldsets = (
        ('Score Details', {
            'fields': ('credit_history', 'factor', 'score')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )


@admin.register(CreditEstimation)
class CreditEstimationAdmin(admin.ModelAdmin):
    list_display = ['user', 'estimated_score', 'confidence_level', 'credit_utilization_percentage', 'created_at']
    list_filter = ['estimated_score', 'confidence_level', 'created_at']
    search_fields = ['user__email']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User & Results', {
            'fields': ('user', 'estimated_score', 'confidence_level')
        }),
        ('Payment History (35%)', {
            'fields': ('missed_payments_count', 'late_payments_count', 'on_time_payments_streak'),
            'classes': ('collapse',),
        }),
        ('Credit Utilization (30%)', {
            'fields': ('total_credit_limit', 'current_credit_usage'),
            'classes': ('collapse',),
        }),
        ('Length of Credit History (15%)', {
            'fields': ('oldest_account_years', 'average_account_age_years'),
            'classes': ('collapse',),
        }),
        ('Credit Mix (10%)', {
            'fields': ('has_credit_cards', 'has_installment_loans', 'has_mortgage', 'has_retail_accounts'),
            'classes': ('collapse',),
        }),
        ('New Credit (10%)', {
            'fields': ('recent_inquiries_count', 'new_accounts_last_year'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at']
    
    def credit_utilization_percentage(self, obj):
        return f"{obj.credit_utilization_percentage:.1f}%"
    credit_utilization_percentage.short_description = 'Credit Utilization'


@admin.register(ImprovementSuggestion)
class ImprovementSuggestionAdmin(admin.ModelAdmin):
    list_display = ['title', 'credit_estimation', 'impact', 'potential_points_gain', 'timeframe_months']
    list_filter = ['impact', 'potential_points_gain', 'timeframe_months']
    search_fields = ['title', 'description', 'credit_estimation__user__email']
    raw_id_fields = ['credit_estimation']
    
    fieldsets = (
        ('Suggestion Details', {
            'fields': ('credit_estimation', 'title', 'description', 'impact')
        }),
        ('Impact & Timeline', {
            'fields': ('potential_points_gain', 'timeframe_months')
        }),
    ) 