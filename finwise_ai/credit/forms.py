from django import forms
from .models import CreditEstimation, CreditFactor, CreditHistory, ImprovementSuggestion

class CreditHistoryForm(forms.ModelForm):
    """Form for recording credit history."""
    
    class Meta:
        model = CreditHistory
        fields = ['date', 'score', 'report_source', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 300, 'max': 850}),
            'report_source': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CreditEstimationForm(forms.ModelForm):
    """Form for estimating credit scores."""
    
    class Meta:
        model = CreditEstimation
        fields = [
            # Payment History
            'missed_payments_count', 'late_payments_count', 'on_time_payments_streak',
            # Credit Utilization
            'total_credit_limit', 'current_credit_usage',
            # Length of Credit History
            'oldest_account_years', 'average_account_age_years',
            # Credit Mix
            'has_credit_cards', 'has_installment_loans', 'has_mortgage', 'has_retail_accounts',
            # New Credit
            'recent_inquiries_count', 'new_accounts_last_year',
        ]
        widgets = {
            # Payment History
            'missed_payments_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'late_payments_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'on_time_payments_streak': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            
            # Credit Utilization
            'total_credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'current_credit_usage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            
            # Length of Credit History
            'oldest_account_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'average_account_age_years': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 0}),
            
            # Credit Mix
            'has_credit_cards': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_installment_loans': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_mortgage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_retail_accounts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # New Credit
            'recent_inquiries_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'new_accounts_last_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        total_credit_limit = cleaned_data.get('total_credit_limit')
        current_credit_usage = cleaned_data.get('current_credit_usage')
        
        if total_credit_limit and current_credit_usage and current_credit_usage > total_credit_limit:
            raise forms.ValidationError("Credit usage cannot exceed credit limit.")
        
        return cleaned_data


class QuickCreditEstimationForm(forms.Form):
    """Simplified form for quick credit score estimation."""
    
    # Basic information
    age = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 18, 'max': 120})
    )
    
    # Payment History (35%)
    ever_missed_payment = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    missed_payments_last_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )
    
    # Credit Utilization (30%)
    has_credit_cards = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    credit_utilization = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select utilization range'),
            ('low', 'Low (0-30%)'),
            ('medium', 'Medium (31-70%)'),
            ('high', 'High (71-100%)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Length of Credit History (15%)
    oldest_account = forms.ChoiceField(
        choices=[
            ('', 'Select age of oldest account'),
            ('less_than_1', 'Less than 1 year'),
            ('1_to_3', '1-3 years'),
            ('3_to_5', '3-5 years'),
            ('5_to_10', '5-10 years'),
            ('more_than_10', 'More than 10 years'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Credit Mix (10%)
    has_loans = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_mortgage = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # New Credit (10%)
    new_credit_last_year = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        has_credit_cards = cleaned_data.get('has_credit_cards')
        credit_utilization = cleaned_data.get('credit_utilization')
        
        if has_credit_cards and not credit_utilization:
            self.add_error('credit_utilization', 'Please select a credit utilization range.')
        
        return cleaned_data
