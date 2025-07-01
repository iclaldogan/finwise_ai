from django.db import models
from accounts.models import User

class LoanType(models.Model):
    """Model for loan types."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=1000000)
    min_term_months = models.IntegerField(default=1)
    max_term_months = models.IntegerField(default=360)  # 30 years
    base_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)  # Percentage
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Loan Type"
        verbose_name_plural = "Loan Types"


class Loan(models.Model):
    """Model for user loans."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paid', 'Paid Off'),
        ('defaulted', 'Defaulted'),
        ('simulated', 'Simulated'),  # For loan simulations
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.ForeignKey(LoanType, on_delete=models.SET_NULL, null=True, related_name='loans')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Annual percentage rate
    term_months = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)  # Null for simulations
    end_date = models.DateField(null=True, blank=True)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='simulated')
    is_simulation = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.loan_type.name if self.loan_type else 'Unknown'} - {self.amount}"
    
    class Meta:
        ordering = ['-created_at']


class LoanPayment(models.Model):
    """Model for tracking loan payments."""
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Payment for {self.loan} on {self.payment_date}"
    
    class Meta:
        ordering = ['payment_date']


class LoanEligibility(models.Model):
    """Model for loan eligibility decisions."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_eligibilities')
    loan_type = models.ForeignKey(LoanType, on_delete=models.CASCADE, related_name='eligibilities')
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested_term_months = models.IntegerField()
    is_eligible = models.BooleanField()
    max_eligible_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    offered_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Eligibility for {self.loan_type.name} - {'Approved' if self.is_eligible else 'Denied'}"
    
    class Meta:
        verbose_name = "Loan Eligibility"
        verbose_name_plural = "Loan Eligibilities"
        ordering = ['-created_at']
