from django.db import models
from accounts.models import User

class CreditFactor(models.Model):
    """Model for credit score factors."""
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    weight = models.IntegerField(default=20)  # Percentage weight in overall score
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Credit Factor"
        verbose_name_plural = "Credit Factors"


class CreditHistory(models.Model):
    """Model for user credit history."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_histories')
    date = models.DateField()
    score = models.IntegerField()  # 300-850 range
    report_source = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Credit Score: {self.score} on {self.date}"
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Credit History"
        verbose_name_plural = "Credit Histories"


class CreditFactorScore(models.Model):
    """Model for individual factor scores within a credit history."""
    
    credit_history = models.ForeignKey(CreditHistory, on_delete=models.CASCADE, related_name='factor_scores')
    factor = models.ForeignKey(CreditFactor, on_delete=models.CASCADE, related_name='scores')
    score = models.IntegerField()  # 0-100 range
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.factor.name}: {self.score}"


class CreditEstimation(models.Model):
    """Model for credit score estimations."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_estimations')
    
    # Payment History (35%)
    missed_payments_count = models.IntegerField(default=0)
    late_payments_count = models.IntegerField(default=0)
    on_time_payments_streak = models.IntegerField(default=0)
    
    # Credit Utilization (30%)
    total_credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_credit_usage = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Length of Credit History (15%)
    oldest_account_years = models.IntegerField(default=0)
    average_account_age_years = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Credit Mix (10%)
    has_credit_cards = models.BooleanField(default=False)
    has_installment_loans = models.BooleanField(default=False)
    has_mortgage = models.BooleanField(default=False)
    has_retail_accounts = models.BooleanField(default=False)
    
    # New Credit (10%)
    recent_inquiries_count = models.IntegerField(default=0)
    new_accounts_last_year = models.IntegerField(default=0)
    
    # Results
    estimated_score = models.IntegerField(null=True, blank=True)
    confidence_level = models.IntegerField(default=0)  # 0-100 range
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.estimated_score:
            return f"Estimated Score: {self.estimated_score} ({self.confidence_level}% confidence)"
        return f"Credit Estimation on {self.created_at.date()}"
    
    @property
    def credit_utilization_percentage(self):
        """Calculate credit utilization percentage."""
        if self.total_credit_limit == 0:
            return 0
        return (self.current_credit_usage / self.total_credit_limit) * 100
    
    class Meta:
        ordering = ['-created_at']


class ImprovementSuggestion(models.Model):
    """Model for credit score improvement suggestions."""
    
    IMPACT_CHOICES = [
        ('high', 'High Impact'),
        ('medium', 'Medium Impact'),
        ('low', 'Low Impact'),
    ]
    
    credit_estimation = models.ForeignKey(CreditEstimation, on_delete=models.CASCADE, related_name='improvement_suggestions')
    title = models.CharField(max_length=255)
    description = models.TextField()
    impact = models.CharField(max_length=10, choices=IMPACT_CHOICES)
    potential_points_gain = models.IntegerField()
    timeframe_months = models.IntegerField()
    is_implemented = models.BooleanField(default=False)
    implemented_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} - {self.get_impact_display()}"
    
    class Meta:
        ordering = ['-potential_points_gain']
