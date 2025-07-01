from django.db import models
from accounts.models import User
from expenses.models import Expense
from loans.models import Loan
from goals.models import SavingsGoal
from investments.models import Investment
from credit.models import CreditHistory

class Dashboard(models.Model):
    """Model for user dashboard preferences and settings."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard')
    show_expenses = models.BooleanField(default=True)
    show_loans = models.BooleanField(default=True)
    show_goals = models.BooleanField(default=True)
    show_investments = models.BooleanField(default=True)
    show_credit = models.BooleanField(default=True)
    
    # Widget order preferences (comma-separated list of widget IDs)
    widget_order = models.CharField(max_length=255, blank=True, null=True)
    
    # Chart preferences
    expense_chart_type = models.CharField(max_length=20, default='pie')  # pie, bar, etc.
    expense_time_period = models.CharField(max_length=20, default='month')  # week, month, year
    investment_chart_type = models.CharField(max_length=20, default='line')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dashboard for {self.user.email}"


class DashboardWidget(models.Model):
    """Model for custom dashboard widgets."""
    
    TYPE_CHOICES = [
        ('expense_summary', 'Expense Summary'),
        ('income_vs_expense', 'Income vs Expense'),
        ('savings_progress', 'Savings Progress'),
        ('loan_summary', 'Loan Summary'),
        ('investment_performance', 'Investment Performance'),
        ('credit_score', 'Credit Score'),
        ('custom', 'Custom Widget'),
    ]
    
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    widget_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=True)
    position = models.IntegerField(default=0)
    size = models.CharField(max_length=20, default='medium')  # small, medium, large
    refresh_interval = models.IntegerField(default=0)  # minutes, 0 for manual refresh
    custom_config = models.JSONField(null=True, blank=True)  # For custom widget configuration
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"
    
    class Meta:
        ordering = ['position']


class Notification(models.Model):
    """Model for user notifications."""
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    related_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional relations to specific entities
    related_expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)
    related_loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True)
    related_goal = models.ForeignKey(SavingsGoal, on_delete=models.SET_NULL, null=True, blank=True)
    related_investment = models.ForeignKey(Investment, on_delete=models.SET_NULL, null=True, blank=True)
    related_credit = models.ForeignKey(CreditHistory, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class FinancialInsight(models.Model):
    """Model for AI-generated financial insights."""
    
    CATEGORY_CHOICES = [
        ('expense', 'Expense Insight'),
        ('saving', 'Saving Opportunity'),
        ('investment', 'Investment Tip'),
        ('budget', 'Budget Alert'),
        ('credit', 'Credit Improvement'),
        ('general', 'General Advice'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_insights')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    importance_score = models.IntegerField(default=5)  # 1-10 scale
    is_read = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-importance_score', '-created_at']
