from django.contrib import admin
from .models import ExpenseCategory, Expense, RecurringExpense, AnomalyDetection


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_default']
    list_filter = ['is_default']
    search_fields = ['name']
    list_editable = ['icon', 'color', 'is_default']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'user', 'category', 'amount', 'date', 'recurrence', 'is_flagged']
    list_filter = ['category', 'recurrence', 'is_flagged', 'date']
    search_fields = ['description', 'user__email', 'notes']
    list_editable = ['is_flagged']
    date_hierarchy = 'date'
    raw_id_fields = ['user']
    autocomplete_fields = ['category']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'category', 'amount', 'description', 'date')
        }),
        ('Recurrence', {
            'fields': ('recurrence', 'recurrence_end_date'),
            'classes': ('collapse',),
        }),
        ('Additional', {
            'fields': ('is_flagged', 'notes'),
            'classes': ('collapse',),
        }),
    )


@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ['parent_expense', 'amount', 'date', 'is_paid', 'is_modified']
    list_filter = ['is_paid', 'is_modified', 'date']
    search_fields = ['parent_expense__description']
    list_editable = ['is_paid', 'is_modified']
    date_hierarchy = 'date'
    raw_id_fields = ['parent_expense']


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'expense', 'anomaly_type', 'confidence_score', 'is_reviewed', 'is_false_positive']
    list_filter = ['anomaly_type', 'is_reviewed', 'is_false_positive', 'created_at']
    search_fields = ['user__email', 'expense__description', 'description']
    list_editable = ['is_reviewed', 'is_false_positive']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'expense']
    
    fieldsets = (
        ('Detection', {
            'fields': ('user', 'expense', 'anomaly_type', 'confidence_score')
        }),
        ('Review', {
            'fields': ('is_reviewed', 'is_false_positive', 'description'),
        }),
    ) 