from django.db import models
from accounts.models import User

class SavingsGoal(models.Model):
    """Model for user savings goals."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='savings_goals')
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    target_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    icon = models.CharField(max_length=50, blank=True, null=True)  # FontAwesome icon class
    color = models.CharField(max_length=20, blank=True, null=True)  # Hex color code
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def progress_percentage(self):
        """Calculate the percentage of goal completion."""
        if self.target_amount == 0:
            return 0
        return min(100, (self.current_amount / self.target_amount) * 100)
    
    @property
    def monthly_target(self):
        """Calculate the monthly savings target to reach the goal."""
        import datetime
        from dateutil.relativedelta import relativedelta
        
        today = datetime.date.today()
        if today > self.target_date:
            return 0
        
        months_remaining = relativedelta(self.target_date, today).months + (12 * relativedelta(self.target_date, today).years)
        if months_remaining == 0:
            return self.target_amount - self.current_amount
        
        return (self.target_amount - self.current_amount) / months_remaining
    
    class Meta:
        ordering = ['target_date']


class GoalContribution(models.Model):
    """Model for tracking contributions to savings goals."""
    
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Contribution to {self.goal.name} - {self.amount}"
    
    def save(self, *args, **kwargs):
        """Override save to update the goal's current amount."""
        super().save(*args, **kwargs)
        
        # Update the goal's current amount
        self.goal.current_amount = sum(
            contribution.amount for contribution in self.goal.contributions.all()
        )
        
        # Check if goal is completed
        if self.goal.current_amount >= self.goal.target_amount:
            self.goal.status = 'completed'
        
        self.goal.save()
    
    class Meta:
        ordering = ['-date']


class GoalMilestone(models.Model):
    """Model for tracking milestones within a savings goal."""
    
    goal = models.ForeignKey(SavingsGoal, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    target_date = models.DateField(null=True, blank=True)
    is_reached = models.BooleanField(default=False)
    reached_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.goal.name}"
    
    class Meta:
        ordering = ['target_amount']
