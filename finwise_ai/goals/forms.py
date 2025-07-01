from django import forms
from .models import SavingsGoal, GoalContribution, GoalMilestone

class SavingsGoalForm(forms.ModelForm):
    """Form for creating and editing savings goals."""
    
    class Meta:
        model = SavingsGoal
        fields = ['name', 'target_amount', 'start_date', 'target_date', 
                 'description', 'status', 'priority', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'placeholder': 'YYYY-MM-DD'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-piggy-bank'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#1DE9B6', 'type': 'color'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        target_date = cleaned_data.get('target_date')
        
        if start_date and target_date and start_date >= target_date:
            raise forms.ValidationError("Target date must be after start date.")
        
        return cleaned_data


class GoalContributionForm(forms.ModelForm):
    """Form for adding contributions to savings goals."""
    
    class Meta:
        model = GoalContribution
        fields = ['amount', 'date', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class GoalMilestoneForm(forms.ModelForm):
    """Form for creating milestones within a savings goal."""
    
    class Meta:
        model = GoalMilestone
        fields = ['name', 'target_amount', 'target_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        goal = kwargs.pop('goal', None)
        super().__init__(*args, **kwargs)
        
        if goal:
            self.fields['target_amount'].widget.attrs.update({
                'max': goal.target_amount,
                'min': 0
            })
            
            if goal.target_date:
                self.fields['target_date'].widget.attrs.update({
                    'max': goal.target_date.isoformat()
                })
    
    def clean(self):
        cleaned_data = super().clean()
        target_amount = cleaned_data.get('target_amount')
        goal = self.instance.goal if hasattr(self.instance, 'goal') else None
        
        if goal and target_amount and target_amount > goal.target_amount:
            raise forms.ValidationError("Milestone target cannot exceed the goal's target amount.")
        
        return cleaned_data


class SavingsPlanForm(forms.Form):
    """Form for generating a savings plan."""
    
    current_savings = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    target_amount = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    target_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    monthly_income = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    monthly_expenses = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    risk_tolerance = forms.ChoiceField(
        choices=[
            ('low', 'Low - Safe and steady'),
            ('medium', 'Medium - Balanced approach'),
            ('high', 'High - Aggressive growth')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        target_date = cleaned_data.get('target_date')
        
        import datetime
        if target_date and target_date <= datetime.date.today():
            raise forms.ValidationError("Target date must be in the future.")
        
        return cleaned_data
