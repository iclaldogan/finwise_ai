from django.db import models
from accounts.models import User

class ExpenseCategory(models.Model):
    """Model for expense categories."""
    
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, null=True)  # FontAwesome icon class
    color = models.CharField(max_length=20, blank=True, null=True)  # Hex color code
    is_default = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"


class Expense(models.Model):
    """Model for user expenses."""
    
    RECURRENCE_CHOICES = [
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='none')
    recurrence_end_date = models.DateField(null=True, blank=True)
    is_flagged = models.BooleanField(default=False)  # For anomaly detection
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.description} - {self.amount}"
    
    class Meta:
        ordering = ['-date']


class RecurringExpense(models.Model):
    """Model for tracking recurring expense instances."""
    
    parent_expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='recurring_instances')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    is_paid = models.BooleanField(default=False)
    is_modified = models.BooleanField(default=False)  # If user modified this instance
    
    def __str__(self):
        return f"{self.parent_expense.description} - {self.date}"
    
    class Meta:
        ordering = ['-date']


class AnomalyDetection(models.Model):
    """Model for expense anomaly detection."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='anomalies')
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='anomalies')
    anomaly_type = models.CharField(max_length=50)  # e.g., 'spike', 'fraud_flag'
    confidence_score = models.FloatField()  # 0.0 to 1.0
    description = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    is_false_positive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.anomaly_type} - {self.expense.description}"
    
    class Meta:
        verbose_name = "Anomaly Detection"
        verbose_name_plural = "Anomaly Detections"
