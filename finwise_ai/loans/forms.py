from django import forms
from .models import LoanType, Loan, LoanEligibility

class LoanTypeForm(forms.ModelForm):
    """Form for creating and editing loan types."""
    
    class Meta:
        model = LoanType
        fields = ['name', 'description', 'min_amount', 'max_amount', 'min_term_months', 
                 'max_term_months', 'base_interest_rate']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'min_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_term_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_term_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'base_interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class LoanForm(forms.ModelForm):
    """Form for creating and editing loans."""
    
    class Meta:
        model = Loan
        fields = ['loan_type', 'amount', 'interest_rate', 'term_months', 'start_date', 
                 'monthly_payment', 'status', 'is_simulation', 'description']
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'term_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monthly_payment': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_simulation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make start_date only required for non-simulation loans
        self.fields['start_date'].required = False


class LoanSimulatorForm(forms.Form):
    """Form for loan simulation."""
    
    LOAN_TYPE_CHOICES = [
        ('personal', 'Personal Loan'),
        ('mortgage', 'Mortgage'),
        ('auto', 'Auto Loan'),
        ('student', 'Student Loan'),
    ]
    
    loan_type = forms.ChoiceField(
        choices=LOAN_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    interest_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    term_years = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '30'})
    )
    monthly_income = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    existing_debt = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )


class LoanEligibilityForm(forms.ModelForm):
    """Form for loan eligibility checks."""
    
    class Meta:
        model = LoanEligibility
        fields = ['loan_type', 'requested_amount', 'requested_term_months']
        widgets = {
            'loan_type': forms.Select(attrs={'class': 'form-select'}),
            'requested_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'requested_term_months': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    # Additional fields for eligibility calculation
    monthly_income = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    existing_monthly_debt = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    credit_score = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '300', 'max': '850'})
    )
    employment_years = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
