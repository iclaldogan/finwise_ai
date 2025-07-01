from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Expense, ExpenseCategory, RecurringExpense, AnomalyDetection
from .forms import ExpenseForm, ExpenseCategoryForm, ExpenseFilterForm, RecurringExpenseForm
import json
import pandas as pd
import numpy as np

@login_required
def expense_home(request):
    """View for the expenses dashboard."""
    # Get filter parameters
    form = ExpenseFilterForm(request.GET, user=request.user)
    
    # Base queryset
    expenses = Expense.objects.filter(user=request.user)
    
    # Apply filters if form is valid
    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            expenses = expenses.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            expenses = expenses.filter(date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('category'):
            expenses = expenses.filter(category=form.cleaned_data['category'])
        if form.cleaned_data.get('min_amount'):
            expenses = expenses.filter(amount__gte=form.cleaned_data['min_amount'])
        if form.cleaned_data.get('max_amount'):
            expenses = expenses.filter(amount__lte=form.cleaned_data['max_amount'])
        if form.cleaned_data.get('description'):
            expenses = expenses.filter(description__icontains=form.cleaned_data['description'])
    
    # Get expense categories for the pie chart
    categories = ExpenseCategory.objects.all()
    category_data = []
    
    for category in categories:
        category_sum = expenses.filter(category=category).aggregate(Sum('amount'))['amount__sum'] or 0
        if category_sum > 0:
            category_data.append({
                'name': category.name,
                'amount': float(category_sum),
                'color': category.color or '#1DE9B6'
            })
    
    # Get monthly totals for the line chart
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)
    
    monthly_expenses = (
        expenses
        .filter(date__gte=six_months_ago)
        .values('date__year', 'date__month')
        .annotate(total=Sum('amount'))
        .order_by('date__year', 'date__month')
    )
    
    monthly_data = []
    for entry in monthly_expenses:
        month_name = datetime(entry['date__year'], entry['date__month'], 1).strftime('%b %Y')
        monthly_data.append({
            'month': month_name,
            'amount': float(entry['total'])
        })
    
    # Get flagged expenses (anomalies)
    flagged_expenses = expenses.filter(is_flagged=True).order_by('-date')[:5]
    
    # Get recurring expenses
    recurring_expenses = expenses.filter(recurrence__in=['daily', 'weekly', 'monthly', 'yearly']).order_by('-date')[:5]
    
    # Calculate this month's expenses
    current_month_start = today.replace(day=1)
    this_month_expenses = expenses.filter(date__gte=current_month_start, date__lte=today)
    this_month_total = this_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate average per day (this month)
    days_in_month = (today - current_month_start).days + 1
    avg_per_day = this_month_total / days_in_month if days_in_month > 0 else 0
    
    context = {
        'expenses': expenses.order_by('-date')[:10],
        'filter_form': form,
        'category_data': json.dumps(category_data),
        'monthly_data': json.dumps(monthly_data),
        'flagged_expenses': flagged_expenses,
        'recurring_expenses': recurring_expenses,
        'total_expenses': expenses.aggregate(Sum('amount'))['amount__sum'] or 0,
        'this_month_total': this_month_total,
        'avg_per_day': avg_per_day,
        'avg_monthly': expenses.filter(date__gte=six_months_ago).aggregate(Avg('amount'))['amount__avg'] or 0,
    }
    
    return render(request, 'expenses/expense_home.html', context)

@login_required
def expense_list(request):
    """View for listing all expenses."""
    # Get filter parameters
    form = ExpenseFilterForm(request.GET, user=request.user)
    
    # Base queryset
    expenses = Expense.objects.filter(user=request.user)
    
    # Apply filters if form is valid
    if form.is_valid():
        if form.cleaned_data.get('start_date'):
            expenses = expenses.filter(date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data.get('end_date'):
            expenses = expenses.filter(date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data.get('category'):
            expenses = expenses.filter(category=form.cleaned_data['category'])
        if form.cleaned_data.get('min_amount'):
            expenses = expenses.filter(amount__gte=form.cleaned_data['min_amount'])
        if form.cleaned_data.get('max_amount'):
            expenses = expenses.filter(amount__lte=form.cleaned_data['max_amount'])
        if form.cleaned_data.get('description'):
            expenses = expenses.filter(description__icontains=form.cleaned_data['description'])
    
    context = {
        'expenses': expenses.order_by('-date'),
        'filter_form': form,
    }
    
    return render(request, 'expenses/expense_list.html', context)

@login_required
def expense_create(request):
    """View for creating a new expense."""
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            
            # Handle recurring expenses
            if expense.recurrence != 'none' and expense.recurrence_end_date:
                create_recurring_expenses(expense)
            
            # Check for anomalies
            detect_anomalies(expense)
            
            messages.success(request, 'Expense created successfully!')
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Add Expense',
        'categories': ExpenseCategory.objects.all(),
    }
    
    return render(request, 'expenses/expense_form.html', context)

@login_required
def expense_edit(request, pk):
    """View for editing an existing expense."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            expense = form.save()
            
            # Update recurring expenses if needed
            if expense.recurrence != 'none':
                update_recurring_expenses(expense)
            
            messages.success(request, 'Expense updated successfully!')
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    
    context = {
        'form': form,
        'expense': expense,
        'title': 'Edit Expense',
        'categories': ExpenseCategory.objects.all(),
    }
    
    return render(request, 'expenses/expense_form.html', context)

@login_required
def expense_delete(request, pk):
    """View for deleting an expense."""
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete recurring instances if this is a recurring expense
        if expense.recurrence != 'none':
            RecurringExpense.objects.filter(parent_expense=expense).delete()
        
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expenses:expense_list')
    
    context = {
        'expense': expense,
    }
    
    return render(request, 'expenses/expense_confirm_delete.html', context)

@login_required
def category_list(request):
    """View for listing expense categories."""
    categories = ExpenseCategory.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'expenses/category_list.html', context)

@login_required
def category_create(request):
    """View for creating a new expense category."""
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('expenses:category_list')
    else:
        form = ExpenseCategoryForm()
    
    context = {
        'form': form,
        'title': 'Add Category',
    }
    
    return render(request, 'expenses/category_form.html', context)

@login_required
def category_edit(request, pk):
    """View for editing an existing expense category."""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('expenses:category_list')
    else:
        form = ExpenseCategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'title': 'Edit Category',
    }
    
    return render(request, 'expenses/category_form.html', context)

@login_required
def category_delete(request, pk):
    """View for deleting an expense category."""
    category = get_object_or_404(ExpenseCategory, pk=pk)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('expenses:category_list')
    
    context = {
        'category': category,
    }
    
    return render(request, 'expenses/category_confirm_delete.html', context)

@login_required
def recurring_expenses(request):
    """View for managing recurring expenses."""
    recurring = RecurringExpense.objects.filter(
        parent_expense__user=request.user,
        date__gte=timezone.now().date()
    ).order_by('date')
    
    context = {
        'recurring_expenses': recurring,
    }
    
    return render(request, 'expenses/recurring_expenses.html', context)

@login_required
def recurring_expense_edit(request, pk):
    """View for editing a recurring expense instance."""
    recurring = get_object_or_404(RecurringExpense, pk=pk, parent_expense__user=request.user)
    
    if request.method == 'POST':
        form = RecurringExpenseForm(request.POST, instance=recurring)
        if form.is_valid():
            recurring = form.save(commit=False)
            recurring.is_modified = True
            recurring.save()
            messages.success(request, 'Recurring expense updated successfully!')
            return redirect('expenses:recurring_expenses')
    else:
        form = RecurringExpenseForm(instance=recurring)
    
    context = {
        'form': form,
        'recurring': recurring,
    }
    
    return render(request, 'expenses/recurring_expense_form.html', context)

@login_required
def anomaly_detection(request):
    """View for displaying expense anomalies."""
    anomalies = AnomalyDetection.objects.filter(
        user=request.user,
        is_reviewed=False
    ).order_by('-created_at')
    
    context = {
        'anomalies': anomalies,
    }
    
    return render(request, 'expenses/anomaly_detection.html', context)

@login_required
def mark_anomaly_reviewed(request, pk):
    """View for marking an anomaly as reviewed."""
    anomaly = get_object_or_404(AnomalyDetection, pk=pk, user=request.user)
    
    if request.method == 'POST':
        is_false_positive = request.POST.get('is_false_positive') == 'true'
        anomaly.is_reviewed = True
        anomaly.is_false_positive = is_false_positive
        anomaly.save()
        
        # If it's not a false positive, keep the expense flagged
        if not is_false_positive:
            anomaly.expense.is_flagged = True
            anomaly.expense.save()
        else:
            anomaly.expense.is_flagged = False
            anomaly.expense.save()
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def expense_analytics(request):
    """View for advanced expense analytics."""
    # Get all expenses for the user
    expenses = Expense.objects.filter(user=request.user)
    
    if not expenses.exists():
        context = {'no_data': True}
        return render(request, 'expenses/expense_analytics.html', context)
    
    # Monthly trend analysis - Use Python date formatting instead of SQL
    from collections import defaultdict
    monthly_totals = defaultdict(float)
    
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        monthly_totals[month_key] += float(expense.amount)
    
    # Sort by month and prepare data
    monthly_data = []
    for month in sorted(monthly_totals.keys()):
        month_display = datetime.strptime(month, '%Y-%m').strftime('%b %Y')
        monthly_data.append({
            'date': month_display,
            'amount': monthly_totals[month]
        })
    
    # Category breakdown
    category_totals = defaultdict(float)
    for expense in expenses:
        category_name = expense.category.name if expense.category else 'Uncategorized'
        category_totals[category_name] += float(expense.amount)
    
    category_data = []
    for category, total in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        category_data.append({
            'category__name': category,
            'amount': total
        })
    
    # Day of week analysis
    day_totals = defaultdict(float)
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for expense in expenses:
        day_name = day_names[expense.date.weekday()]
        day_totals[day_name] += float(expense.amount)
    
    day_data = []
    for day in day_names:
        if day in day_totals:
            day_data.append({
                'day_of_week': day,
                'amount': day_totals[day]
            })
    
    # Largest expenses
    largest_expenses = expenses.order_by('-amount')[:10]
    
    # Prepare data for Chart.js
    monthly_trend_json = json.dumps(monthly_data)
    category_breakdown_json = json.dumps(category_data)
    
    # Calculate totals
    total_expenses = sum(float(expense.amount) for expense in expenses)
    num_transactions = expenses.count()
    avg_monthly = total_expenses / len(monthly_data) if monthly_data else 0
    
    context = {
        'monthly_trend': monthly_trend_json,
        'category_breakdown': category_breakdown_json,
        'day_of_week': day_data,
        'largest_expenses': largest_expenses,
        'total_expenses': total_expenses,
        'avg_monthly': avg_monthly,
        'num_transactions': num_transactions,
    }
    
    return render(request, 'expenses/expense_analytics.html', context)

# Helper functions

def create_recurring_expenses(expense):
    """Create recurring expense instances based on the recurrence pattern."""
    from dateutil.relativedelta import relativedelta
    
    start_date = expense.date
    end_date = expense.recurrence_end_date
    
    current_date = start_date
    
    while current_date <= end_date:
        if current_date > start_date:  # Skip the first one (it's the original expense)
            RecurringExpense.objects.create(
                parent_expense=expense,
                amount=expense.amount,
                date=current_date,
                is_paid=False
            )
        
        # Calculate next date based on recurrence pattern
        if expense.recurrence == 'daily':
            current_date += timedelta(days=1)
        elif expense.recurrence == 'weekly':
            current_date += timedelta(weeks=1)
        elif expense.recurrence == 'monthly':
            current_date += relativedelta(months=1)
        elif expense.recurrence == 'yearly':
            current_date += relativedelta(years=1)

def update_recurring_expenses(expense):
    """Update recurring expense instances after the parent expense is modified."""
    # Delete future recurring instances that haven't been modified
    RecurringExpense.objects.filter(
        parent_expense=expense,
        date__gt=timezone.now().date(),
        is_modified=False
    ).delete()
    
    # Create new recurring instances
    if expense.recurrence != 'none' and expense.recurrence_end_date:
        create_recurring_expenses(expense)

def detect_anomalies(expense):
    """Detect anomalies in expenses using simple statistical methods."""
    # Get user's expenses in the same category from the last 6 months
    six_months_ago = timezone.now().date() - timedelta(days=180)
    category_expenses = Expense.objects.filter(
        user=expense.user,
        category=expense.category,
        date__gte=six_months_ago,
        date__lt=expense.date  # Exclude the current expense
    )
    
    if category_expenses.count() >= 5:  # Need enough data for meaningful analysis
        # Calculate mean and standard deviation
        amounts = [e.amount for e in category_expenses]
        mean = np.mean(amounts)
        std_dev = np.std(amounts)
        
        # Check if current expense is an outlier (> 2 standard deviations from mean)
        if expense.amount > mean + (2 * std_dev):
            # Create anomaly detection record
            AnomalyDetection.objects.create(
                user=expense.user,
                expense=expense,
                anomaly_type='spike',
                confidence_score=min(1.0, (expense.amount - mean) / (3 * std_dev)),
                description=f"This expense is significantly higher than your usual spending in this category. Average: {mean:.2f}, This expense: {expense.amount:.2f}"
            )
            
            # Flag the expense
            expense.is_flagged = True
            expense.save()
