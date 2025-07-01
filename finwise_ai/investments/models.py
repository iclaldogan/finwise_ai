from django.db import models
from accounts.models import User

class InvestmentType(models.Model):
    """Model for investment types."""
    
    CATEGORY_CHOICES = [
        ('stocks', 'Stocks'),
        ('bonds', 'Bonds'),
        ('mutual_funds', 'Mutual Funds'),
        ('crypto', 'Cryptocurrencies'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    risk_level = models.IntegerField(default=3)  # 1-5 scale, 5 being highest risk
    avg_annual_return = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Historical average
    volatility = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Standard deviation
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    class Meta:
        verbose_name = "Investment Type"
        verbose_name_plural = "Investment Types"


class Investment(models.Model):
    """Model for user investments."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('simulated', 'Simulated'),  # For investment simulations
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    investment_type = models.ForeignKey(InvestmentType, on_delete=models.SET_NULL, null=True, related_name='investments')
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=20, blank=True, null=True)  # Stock/crypto symbol
    purchase_date = models.DateField(null=True, blank=True)  # Null for simulations
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=6)  # Allow fractional shares/units
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_simulation = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.quantity} units"
    
    @property
    def current_value(self):
        """Calculate the current value of the investment."""
        if self.current_price:
            return self.current_price * self.quantity
        return self.purchase_price * self.quantity
    
    @property
    def profit_loss(self):
        """Calculate the profit or loss on the investment."""
        if self.current_price:
            return (self.current_price - self.purchase_price) * self.quantity
        return 0
    
    @property
    def profit_loss_percentage(self):
        """Calculate the profit or loss percentage on the investment."""
        if self.purchase_price == 0:
            return 0
        if self.current_price:
            return ((self.current_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    class Meta:
        ordering = ['-created_at']


class InvestmentTransaction(models.Model):
    """Model for tracking investment transactions."""
    
    TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
        ('split', 'Stock Split'),
        ('other', 'Other'),
    ]
    
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date = models.DateField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.DecimalField(max_digits=12, decimal_places=6)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.investment.name} - {self.quantity} units"
    
    class Meta:
        ordering = ['-date']


class InvestmentSimulation(models.Model):
    """Model for investment simulations."""
    
    STRATEGY_CHOICES = [
        ('lump_sum', 'Lump Sum'),
        ('dca', 'Dollar Cost Averaging'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investment_simulations')
    investment_type = models.ForeignKey(InvestmentType, on_delete=models.SET_NULL, null=True, related_name='simulations')
    name = models.CharField(max_length=255)
    strategy = models.CharField(max_length=10, choices=STRATEGY_CHOICES)
    initial_amount = models.DecimalField(max_digits=12, decimal_places=2)
    periodic_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # For DCA
    period_months = models.IntegerField(default=1)  # Frequency for DCA
    duration_years = models.IntegerField()
    expected_return = models.DecimalField(max_digits=5, decimal_places=2)  # Annual percentage
    volatility = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Standard deviation
    inflation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Annual percentage
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_strategy_display()}"
    
    class Meta:
        ordering = ['-created_at']


class SimulationResult(models.Model):
    """Model for storing investment simulation results."""
    
    simulation = models.ForeignKey(InvestmentSimulation, on_delete=models.CASCADE, related_name='results')
    year = models.IntegerField()
    month = models.IntegerField()
    investment_value = models.DecimalField(max_digits=12, decimal_places=2)
    cumulative_investment = models.DecimalField(max_digits=12, decimal_places=2)
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"Result for {self.simulation.name} - Year {self.year}, Month {self.month}"
    
    class Meta:
        ordering = ['year', 'month']
