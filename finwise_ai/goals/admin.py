from django.contrib import admin
from .models import SavingsGoal, GoalContribution, GoalMilestone


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'target_amount', 'current_amount', 'progress_percentage', 'status', 'priority', 'target_date']
    list_filter = ['status', 'priority', 'target_date', 'created_at']
    search_fields = ['name', 'user__email', 'description']
    list_editable = ['status', 'priority']
    date_hierarchy = 'target_date'
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description', 'priority')
        }),
        ('Financial Details', {
            'fields': ('target_amount', 'current_amount', 'start_date', 'target_date')
        }),
        ('Display', {
            'fields': ('icon', 'color'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status',),
        }),
    )
    
    readonly_fields = ['current_amount']
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = 'Progress'


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ['goal', 'amount', 'date', 'created_at']
    list_filter = ['date', 'created_at']
    search_fields = ['goal__name', 'notes']
    date_hierarchy = 'date'
    raw_id_fields = ['goal']
    
    fieldsets = (
        ('Contribution Details', {
            'fields': ('goal', 'amount', 'date')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )


@admin.register(GoalMilestone)
class GoalMilestoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'goal', 'target_amount', 'target_date', 'is_reached', 'reached_date']
    list_filter = ['is_reached', 'target_date', 'reached_date']
    search_fields = ['name', 'goal__name']
    list_editable = ['is_reached', 'reached_date']
    date_hierarchy = 'target_date'
    raw_id_fields = ['goal']
    
    fieldsets = (
        ('Milestone Details', {
            'fields': ('goal', 'name', 'target_amount', 'target_date')
        }),
        ('Achievement', {
            'fields': ('is_reached', 'reached_date'),
        }),
    ) 