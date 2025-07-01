from django import forms
from .models import Conversation, Message, PromptTemplate, UserQuery

class ConversationForm(forms.ModelForm):
    """Form for creating and managing conversations."""
    
    class Meta:
        model = Conversation
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MessageForm(forms.ModelForm):
    """Form for creating messages in a conversation."""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your message here...'}),
        }


class PromptTemplateForm(forms.ModelForm):
    """Form for creating and editing prompt templates."""
    
    class Meta:
        model = PromptTemplate
        fields = ['name', 'description', 'category', 'template_text', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'template_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserQueryForm(forms.ModelForm):
    """Form for submitting user queries to the AI assistant."""
    
    class Meta:
        model = UserQuery
        fields = ['query_text']
        widgets = {
            'query_text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Ask me anything about your finances...'
            }),
        }


class AIAssistantForm(forms.Form):
    """Form for interacting with the AI assistant."""
    
    query = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Example: "Analyze my last 3 months\' expenses and help me save ₺5,000 more."'
        })
    )
    
    CONTEXT_CHOICES = [
        ('all', 'All Financial Data'),
        ('expenses', 'Expenses Only'),
        ('investments', 'Investments Only'),
        ('loans', 'Loans Only'),
        ('goals', 'Savings Goals Only'),
        ('credit', 'Credit Score Only'),
    ]
    
    context = forms.ChoiceField(
        choices=CONTEXT_CHOICES,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    time_period = forms.ChoiceField(
        choices=[
            ('1m', 'Last Month'),
            ('3m', 'Last 3 Months'),
            ('6m', 'Last 6 Months'),
            ('1y', 'Last Year'),
            ('all', 'All Time'),
        ],
        initial='3m',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
