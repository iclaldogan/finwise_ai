from django import forms
from .models import InvestmentType, Investment, InvestmentSimulation

class InvestmentTypeForm(forms.ModelForm):
    """Form for creating and editing investment types."""
    
    class Meta:
        model = InvestmentType
        fields = ['name', 'category', 'description', 'risk_level', 'avg_annual_return', 'volatility']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'risk_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'avg_annual_return': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volatility': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class InvestmentForm(forms.ModelForm):
    """Form for creating and editing investments."""
    
    class Meta:
        model = Investment
        fields = ['investment_type', 'name', 'symbol', 'purchase_date', 'purchase_price', 
                 'quantity', 'status', 'is_simulation', 'notes']
        widgets = {
            'investment_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_simulation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make purchase_date only required for non-simulation investments
        self.fields['purchase_date'].required = False


class InvestmentTransactionForm(forms.Form):
    """Form for recording investment transactions."""
    
    TRANSACTION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
        ('split', 'Stock Split'),
        ('other', 'Other'),
    ]
    
    transaction_type = forms.ChoiceField(
        choices=TRANSACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    price = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    quantity = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'})
    )
    fees = forms.DecimalField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )


class InvestmentSimulationForm(forms.ModelForm):
    """Form for creating investment simulations."""
    
    class Meta:
        model = InvestmentSimulation
        fields = ['investment_type', 'name', 'strategy', 'initial_amount', 'periodic_amount',
                 'period_months', 'duration_years', 'expected_return', 'volatility', 'inflation_rate']
        widgets = {
            'investment_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'strategy': forms.Select(attrs={'class': 'form-select'}),
            'initial_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'periodic_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'period_months': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duration_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'expected_return': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'volatility': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'inflation_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        strategy = cleaned_data.get('strategy')
        periodic_amount = cleaned_data.get('periodic_amount')
        
        if strategy == 'dca' and (periodic_amount is None or periodic_amount <= 0):
            raise forms.ValidationError("Periodic amount must be greater than zero for Dollar Cost Averaging strategy.")
        
        return cleaned_data
