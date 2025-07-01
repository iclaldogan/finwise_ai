from django import forms
from .models import Dashboard, DashboardWidget, Notification, FinancialInsight

class DashboardPreferencesForm(forms.ModelForm):
    """Form for user dashboard preferences."""
    
    class Meta:
        model = Dashboard
        fields = [
            'show_expenses', 'show_loans', 'show_goals', 
            'show_investments', 'show_credit',
            'expense_chart_type', 'expense_time_period', 'investment_chart_type'
        ]
        widgets = {
            'show_expenses': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_loans': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_goals': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_investments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_credit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'expense_chart_type': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('pie', 'Pie Chart'),
                ('bar', 'Bar Chart'),
                ('doughnut', 'Doughnut Chart'),
            ]),
            'expense_time_period': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('week', 'Weekly'),
                ('month', 'Monthly'),
                ('quarter', 'Quarterly'),
                ('year', 'Yearly'),
            ]),
            'investment_chart_type': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('line', 'Line Chart'),
                ('bar', 'Bar Chart'),
                ('area', 'Area Chart'),
            ]),
        }


class DashboardWidgetForm(forms.ModelForm):
    """Form for creating and editing dashboard widgets."""
    
    class Meta:
        model = DashboardWidget
        fields = ['widget_type', 'title', 'is_enabled', 'position', 'size', 'refresh_interval']
        widgets = {
            'widget_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'position': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'size': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('small', 'Small'),
                ('medium', 'Medium'),
                ('large', 'Large'),
            ]),
            'refresh_interval': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class NotificationForm(forms.ModelForm):
    """Form for creating notifications."""
    
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'related_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'related_url': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FinancialInsightForm(forms.ModelForm):
    """Form for creating financial insights."""
    
    class Meta:
        model = FinancialInsight
        fields = ['title', 'description', 'category', 'importance_score']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'importance_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
        }


class DateRangeFilterForm(forms.Form):
    """Form for filtering dashboard data by date range."""
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data
