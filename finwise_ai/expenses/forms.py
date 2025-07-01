from django import forms
from .models import ExpenseCategory, Expense, RecurringExpense

class ExpenseCategoryForm(forms.ModelForm):
    """Form for creating and editing expense categories."""
    
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-shopping-cart'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#1DE9B6', 'type': 'color'}),
        }


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expenses."""
    
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'date', 'recurrence', 'recurrence_end_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'recurrence': forms.Select(attrs={'class': 'form-select'}),
            'recurrence_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show categories available to this user
        if user:
            # This would need to be adjusted based on how you handle categories
            # Either filter by user-specific categories or show all default categories
            self.fields['category'].queryset = ExpenseCategory.objects.all()
        
        # Make recurrence end date only required if recurrence is not 'none'
        self.fields['recurrence_end_date'].required = False


class ExpenseFilterForm(forms.Form):
    """Form for filtering expenses."""
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    min_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    max_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show categories available to this user
        if user:
            # This would need to be adjusted based on how you handle categories
            self.fields['category'].queryset = ExpenseCategory.objects.all()


class RecurringExpenseForm(forms.ModelForm):
    """Form for editing recurring expense instances."""
    
    class Meta:
        model = RecurringExpense
        fields = ['amount', 'date', 'is_paid']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
