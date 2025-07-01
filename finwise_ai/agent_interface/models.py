from django.db import models
from accounts.models import User
from expenses.models import Expense
from loans.models import Loan
from goals.models import SavingsGoal
from investments.models import Investment
from credit.models import CreditEstimation

class Conversation(models.Model):
    """Model for AI assistant conversations."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    """Model for messages within a conversation."""
    
    TYPE_CHOICES = [
        ('user', 'User Message'),
        ('assistant', 'Assistant Message'),
        ('system', 'System Message'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional relations to specific entities referenced in the message
    related_expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)
    related_loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True)
    related_goal = models.ForeignKey(SavingsGoal, on_delete=models.SET_NULL, null=True, blank=True)
    related_investment = models.ForeignKey(Investment, on_delete=models.SET_NULL, null=True, blank=True)
    related_credit = models.ForeignKey(CreditEstimation, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_message_type_display()}: {self.content[:50]}..."
    
    class Meta:
        ordering = ['created_at']


class PromptTemplate(models.Model):
    """Model for AI assistant prompt templates."""
    
    CATEGORY_CHOICES = [
        ('expense_analysis', 'Expense Analysis'),
        ('budget_planning', 'Budget Planning'),
        ('investment_advice', 'Investment Advice'),
        ('debt_management', 'Debt Management'),
        ('savings_strategy', 'Savings Strategy'),
        ('credit_improvement', 'Credit Improvement'),
        ('general', 'General Financial Advice'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    template_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['category', 'name']


class UserQuery(models.Model):
    """Model for tracking and analyzing user queries."""
    
    INTENT_CHOICES = [
        ('expense_analysis', 'Expense Analysis'),
        ('budget_planning', 'Budget Planning'),
        ('investment_advice', 'Investment Advice'),
        ('debt_management', 'Debt Management'),
        ('savings_strategy', 'Savings Strategy'),
        ('credit_improvement', 'Credit Improvement'),
        ('general_question', 'General Question'),
        ('unknown', 'Unknown Intent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='queries')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField()
    detected_intent = models.CharField(max_length=20, choices=INTENT_CHOICES, default='unknown')
    confidence_score = models.FloatField(default=0.0)  # 0.0 to 1.0
    processed_successfully = models.BooleanField(default=False)
    processing_time = models.FloatField(null=True, blank=True)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.query_text[:50]}... ({self.get_detected_intent_display()})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Query"
        verbose_name_plural = "User Queries"


class AgentAction(models.Model):
    """Model for tracking actions taken by the AI agent."""
    
    ACTION_CHOICES = [
        ('data_retrieval', 'Data Retrieval'),
        ('calculation', 'Calculation'),
        ('recommendation', 'Recommendation'),
        ('notification', 'Notification'),
        ('goal_creation', 'Goal Creation'),
        ('expense_categorization', 'Expense Categorization'),
        ('other', 'Other Action'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user_query = models.ForeignKey(UserQuery, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=25, choices=ACTION_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    result = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_action_type_display()}: {self.status}"
    
    class Meta:
        ordering = ['-created_at']
