from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from accounts.models import UserProfile
from expenses.models import Expense, ExpenseCategory
from loans.models import Loan
from goals.models import SavingsGoal
from investments.models import Investment
from credit.models import CreditHistory

@login_required
def dashboard_home(request):
    """Main dashboard view showing overview of all financial data."""
    # Get current date and date ranges
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    # Get user's expenses for current month
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start,
        date__lte=today
    )
    
    # Get user's expenses for last month
    last_month_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=last_month_start,
        date__lt=current_month_start
    )
    
    # Calculate total expenses for current and last month
    current_month_total = sum(expense.amount for expense in current_month_expenses)
    last_month_total = sum(expense.amount for expense in last_month_expenses)
    
    # Calculate month-over-month change
    if last_month_total > 0:
        mom_change = ((current_month_total - last_month_total) / last_month_total) * 100
    else:
        mom_change = 0
    
    # Get expense breakdown by category for current month
    categories = ExpenseCategory.objects.all()
    expense_breakdown = []
    
    for category in categories:
        category_expenses = current_month_expenses.filter(category=category)
        category_total = sum(expense.amount for expense in category_expenses)
        
        if category_total > 0:
            expense_breakdown.append({
                'category': category.name,
                'amount': category_total,
                'percentage': (category_total / current_month_total * 100) if current_month_total > 0 else 0
            })
    
    # Sort expense breakdown by amount (descending)
    expense_breakdown = sorted(expense_breakdown, key=lambda x: x['amount'], reverse=True)
    
    # Get user's income
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        monthly_income = user_profile.monthly_income
    except UserProfile.DoesNotExist:
        monthly_income = 0
    
    # Calculate savings rate
    if monthly_income and monthly_income > 0:
        savings_rate = ((monthly_income - current_month_total) / monthly_income) * 100
    else:
        savings_rate = 0
    
    # Get active loans
    active_loans = Loan.objects.filter(
        user=request.user,
        status='active'
    )
    
    total_loan_balance = sum(loan.remaining_balance or loan.amount for loan in active_loans)
    
    # Get savings goals
    savings_goals = SavingsGoal.objects.filter(
        user=request.user,
        status='active'
    ).order_by('target_date')
    
    # Calculate progress for each goal
    for goal in savings_goals:
        goal.progress_percentage = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
    
    # Get investment portfolio
    investments = Investment.objects.filter(
        user=request.user,
        status='active',
        is_simulation=False
    )
    
    total_investment_value = sum(inv.current_value for inv in investments)
    total_investment_cost = sum(inv.purchase_price * inv.quantity for inv in investments)
    
    # Calculate investment return
    if total_investment_cost > 0:
        investment_return = ((total_investment_value - total_investment_cost) / total_investment_cost) * 100
    else:
        investment_return = 0
    
    # Get latest credit score
    latest_credit = CreditHistory.objects.filter(
        user=request.user
    ).order_by('-date').first()
    
    credit_score = latest_credit.score if latest_credit else None
    
    # Get weekly spending trend (last 4 weeks)
    weekly_spending = []
    
    for i in range(4, 0, -1):
        week_end = today - timedelta(days=today.weekday() + 1 + (7 * (i - 1)))
        week_start = week_end - timedelta(days=6)
        
        week_expenses = Expense.objects.filter(
            user=request.user,
            date__gte=week_start,
            date__lte=week_end
        )
        
        week_total = sum(expense.amount for expense in week_expenses)
        
        weekly_spending.append({
            'week': f'Week {5-i}',
            'start_date': week_start.strftime('%m/%d'),
            'end_date': week_end.strftime('%m/%d'),
            'amount': week_total
        })
    
    # Prepare context for template
    context = {
        'current_month_total': current_month_total,
        'last_month_total': last_month_total,
        'mom_change': mom_change,
        'expense_breakdown': expense_breakdown,
        'monthly_income': monthly_income,
        'savings_rate': savings_rate,
        'active_loans': active_loans,
        'total_loan_balance': total_loan_balance,
        'savings_goals': savings_goals,
        'total_investment_value': total_investment_value,
        'investment_return': investment_return,
        'credit_score': credit_score,
        'weekly_spending': weekly_spending,
        'expense_breakdown_json': json.dumps([{
            'category': item['category'],
            'amount': float(item['amount']),
            'percentage': float(item['percentage'])
        } for item in expense_breakdown]),
        'weekly_spending_json': json.dumps([{
            'week': item['week'],
            'amount': float(item['amount'])
        } for item in weekly_spending])
    }
    
    return render(request, 'dashboard/dashboard_home.html', context)

@login_required
def financial_summary(request):
    """View for displaying a comprehensive financial summary."""
    # Get user profile
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None
    
    # Calculate net worth
    assets = calculate_total_assets(request.user)
    liabilities = calculate_total_liabilities(request.user)
    net_worth = assets - liabilities
    
    # Calculate debt-to-income ratio
    monthly_debt_payments = calculate_monthly_debt_payments(request.user)
    monthly_income = user_profile.monthly_income if user_profile else 0
    
    if monthly_income > 0:
        debt_to_income = (monthly_debt_payments / monthly_income) * 100
    else:
        debt_to_income = 0
    
    # Calculate emergency fund coverage
    monthly_expenses = calculate_average_monthly_expenses(request.user)
    emergency_fund = user_profile.emergency_fund if user_profile else 0
    
    if monthly_expenses > 0:
        emergency_fund_months = emergency_fund / monthly_expenses
    else:
        emergency_fund_months = 0
    
    # Calculate savings rate (last 3 months)
    savings_rate = calculate_savings_rate(request.user)
    
    # Get financial health score
    financial_health_score = calculate_financial_health_score(
        debt_to_income, emergency_fund_months, savings_rate
    )
    
    context = {
        'assets': assets,
        'liabilities': liabilities,
        'net_worth': net_worth,
        'debt_to_income': debt_to_income,
        'monthly_debt_payments': monthly_debt_payments,
        'monthly_income': monthly_income,
        'emergency_fund': emergency_fund,
        'emergency_fund_months': emergency_fund_months,
        'savings_rate': savings_rate,
        'financial_health_score': financial_health_score
    }
    
    return render(request, 'dashboard/financial_summary.html', context)

@login_required
def expense_trends(request):
    """View for analyzing expense trends over time."""
    # Get date range from request or use default (last 6 months)
    months = int(request.GET.get('months', 6))
    
    # Calculate date range
    today = timezone.now().date()
    end_date = today
    start_date = (today - timedelta(days=today.day - 1)).replace(month=((today.month - months - 1) % 12) + 1)
    
    if start_date.month > today.month:
        start_date = start_date.replace(year=today.year - 1)
    
    # Get expenses in date range
    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Group expenses by month and category
    monthly_expenses = {}
    categories = ExpenseCategory.objects.all()
    
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        
        if month_key not in monthly_expenses:
            monthly_expenses[month_key] = {
                'month': expense.date.strftime('%b %Y'),
                'total': 0,
                'categories': {category.name: 0 for category in categories}
            }
        
        monthly_expenses[month_key]['total'] += expense.amount
        monthly_expenses[month_key]['categories'][expense.category.name] += expense.amount
    
    # Convert to list and sort by month
    monthly_data = list(monthly_expenses.values())
    
    # Calculate month-over-month changes
    for i in range(1, len(monthly_data)):
        prev_total = monthly_data[i-1]['total']
        curr_total = monthly_data[i]['total']
        
        if prev_total > 0:
            monthly_data[i]['mom_change'] = ((curr_total - prev_total) / prev_total) * 100
        else:
            monthly_data[i]['mom_change'] = 0
    
    # Prepare data for charts
    months = [data['month'] for data in monthly_data]
    totals = [float(data['total']) for data in monthly_data]
    
    category_data = {}
    for category in categories:
        category_data[category.name] = [float(data['categories'][category.name]) for data in monthly_data]
    
    context = {
        'monthly_data': monthly_data,
        'months': json.dumps(months),
        'totals': json.dumps(totals),
        'category_data': json.dumps(category_data),
        'selected_months': months
    }
    
    return render(request, 'dashboard/expense_trends.html', context)

@login_required
def income_vs_expenses(request):
    """View for comparing income vs expenses over time."""
    # Get date range from request or use default (last 12 months)
    months = int(request.GET.get('months', 12))
    
    # Calculate date range
    today = timezone.now().date()
    end_date = today
    start_date = (today - timedelta(days=today.day - 1)).replace(month=((today.month - months - 1) % 12) + 1)
    
    if start_date.month > today.month:
        start_date = start_date.replace(year=today.year - 1)
    
    # Get user profile for income
    user_profile = UserProfile.objects.get(user=request.user)
    monthly_income = user_profile.monthly_income
    
    # Get expenses in date range
    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Group expenses by month
    monthly_data = {}
    
    # Initialize with income for all months in range
    current_date = start_date
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        month_name = current_date.strftime('%b %Y')
        
        monthly_data[month_key] = {
            'month': month_name,
            'income': monthly_income,
            'expenses': 0,
            'savings': monthly_income  # Will subtract expenses later
        }
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Add expenses to monthly data
    for expense in expenses:
        month_key = expense.date.strftime('%Y-%m')
        
        if month_key in monthly_data:
            monthly_data[month_key]['expenses'] += expense.amount
            monthly_data[month_key]['savings'] = monthly_data[month_key]['income'] - monthly_data[month_key]['expenses']
    
    # Convert to list and sort by month
    monthly_data = list(monthly_data.values())
    
    # Calculate savings rate for each month
    for data in monthly_data:
        if data['income'] > 0:
            data['savings_rate'] = (data['savings'] / data['income']) * 100
        else:
            data['savings_rate'] = 0
    
    # Prepare data for charts
    months = [data['month'] for data in monthly_data]
    income = [float(data['income']) for data in monthly_data]
    expenses = [float(data['expenses']) for data in monthly_data]
    savings = [float(data['savings']) for data in monthly_data]
    savings_rate = [float(data['savings_rate']) for data in monthly_data]
    
    context = {
        'monthly_data': monthly_data,
        'months': json.dumps(months),
        'income': json.dumps(income),
        'expenses': json.dumps(expenses),
        'savings': json.dumps(savings),
        'savings_rate': json.dumps(savings_rate),
        'selected_months': months
    }
    
    return render(request, 'dashboard/income_vs_expenses.html', context)

@login_required
def net_worth_tracker(request):
    """View for tracking net worth over time."""
    # Calculate current net worth
    assets = calculate_total_assets(request.user)
    liabilities = calculate_total_liabilities(request.user)
    net_worth = assets - liabilities
    
    # Get historical net worth data (if available)
    # In a real app, this would come from a NetWorthHistory model
    # For this demo, we'll generate some sample data
    
    # Generate monthly data for the last 12 months
    today = timezone.now().date()
    
    net_worth_history = []
    current_net_worth = net_worth
    
    for i in range(12, 0, -1):
        month_date = today.replace(day=1)
        if month_date.month <= i:
            month_date = month_date.replace(year=month_date.year - 1, month=12 - (i - month_date.month))
        else:
            month_date = month_date.replace(month=month_date.month - i)
        
        # Simulate some random fluctuation in past net worth
        random_factor = 1 + (np.random.random() * 0.05 - 0.025)  # +/- 2.5%
        historical_net_worth = current_net_worth * random_factor * (0.97 ** i)  # Assume 3% monthly growth
        
        net_worth_history.append({
            'date': month_date,
            'assets': historical_net_worth * 0.7,  # Assume 70% assets, 30% liabilities
            'liabilities': historical_net_worth * 0.3 * -1,  # Negative for liabilities
            'net_worth': historical_net_worth
        })
    
    # Add current month
    net_worth_history.append({
        'date': today.replace(day=1),
        'assets': assets,
        'liabilities': liabilities * -1,  # Negative for liabilities
        'net_worth': net_worth
    })
    
    # Sort by date
    net_worth_history = sorted(net_worth_history, key=lambda x: x['date'])
    
    # Prepare data for charts
    dates = [item['date'].strftime('%b %Y') for item in net_worth_history]
    assets_data = [float(item['assets']) for item in net_worth_history]
    liabilities_data = [float(item['liabilities']) for item in net_worth_history]
    net_worth_data = [float(item['net_worth']) for item in net_worth_history]
    
    # Calculate growth
    if len(net_worth_history) > 1:
        first_net_worth = net_worth_history[0]['net_worth']
        last_net_worth = net_worth_history[-1]['net_worth']
        
        if first_net_worth > 0:
            growth_percentage = ((last_net_worth - first_net_worth) / first_net_worth) * 100
        else:
            growth_percentage = 0
    else:
        growth_percentage = 0
    
    context = {
        'current_assets': assets,
        'current_liabilities': liabilities,
        'current_net_worth': net_worth,
        'net_worth_history': net_worth_history,
        'dates': json.dumps(dates),
        'assets_data': json.dumps(assets_data),
        'liabilities_data': json.dumps(liabilities_data),
        'net_worth_data': json.dumps(net_worth_data),
        'growth_percentage': growth_percentage
    }
    
    return render(request, 'dashboard/net_worth_tracker.html', context)

@login_required
def financial_goals_progress(request):
    """View for tracking progress towards financial goals."""
    # Get all savings goals
    savings_goals = SavingsGoal.objects.filter(
        user=request.user
    ).order_by('target_date')
    
    # Calculate progress for each goal
    for goal in savings_goals:
        goal.progress_percentage = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
        
        # Calculate monthly contribution needed
        if not goal.is_completed:
            today = timezone.now().date()
            months_remaining = max(1, (goal.target_date.year - today.year) * 12 + goal.target_date.month - today.month)
            amount_remaining = goal.target_amount - goal.current_amount
            
            if months_remaining > 0:
                goal.monthly_contribution_needed = amount_remaining / months_remaining
            else:
                goal.monthly_contribution_needed = amount_remaining
        else:
            goal.monthly_contribution_needed = 0
    
    # Separate active and completed goals
    active_goals = [goal for goal in savings_goals if not goal.is_completed]
    completed_goals = [goal for goal in savings_goals if goal.is_completed]
    
    # Prepare data for charts
    goal_names = [goal.name for goal in active_goals]
    goal_progress = [float(goal.progress_percentage) for goal in active_goals]
    goal_remaining = [float(100 - goal.progress_percentage) for goal in active_goals]
    
    context = {
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'goal_names': json.dumps(goal_names),
        'goal_progress': json.dumps(goal_progress),
        'goal_remaining': json.dumps(goal_remaining)
    }
    
    return render(request, 'dashboard/financial_goals_progress.html', context)

@login_required
def budget_performance(request):
    """View for analyzing budget performance."""
    # Get current month
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    current_month_end = (current_month_start.replace(month=current_month_start.month % 12 + 1, day=1) - timedelta(days=1)) if current_month_start.month < 12 else current_month_start.replace(year=current_month_start.year + 1, month=1, day=1) - timedelta(days=1)
    
    # Get user's budget categories
    # In a real app, this would come from a Budget model
    # For this demo, we'll use expense categories and generate some budget amounts
    
    categories = ExpenseCategory.objects.all()
    
    # Get user profile for income
    user_profile = UserProfile.objects.get(user=request.user)
    monthly_income = user_profile.monthly_income
    
    # Generate budget amounts (50% of income distributed across categories)
    total_budget = monthly_income * 0.5
    budget_per_category = total_budget / len(categories)
    
    # Get expenses for current month
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start,
        date__lte=current_month_end
    )
    
    # Calculate budget performance
    budget_performance = []
    
    for category in categories:
        category_expenses = current_month_expenses.filter(category=category)
        category_total = sum(expense.amount for expense in category_expenses)
        
        budget_performance.append({
            'category': category.name,
            'budget': budget_per_category,
            'actual': category_total,
            'difference': budget_per_category - category_total,
            'percentage': (category_total / budget_per_category * 100) if budget_per_category > 0 else 0
        })
    
    # Sort by percentage (descending)
    budget_performance = sorted(budget_performance, key=lambda x: x['percentage'], reverse=True)
    
    # Prepare data for charts
    categories_list = [item['category'] for item in budget_performance]
    budget_amounts = [float(item['budget']) for item in budget_performance]
    actual_amounts = [float(item['actual']) for item in budget_performance]
    
    context = {
        'budget_performance': budget_performance,
        'categories': json.dumps(categories_list),
        'budget_amounts': json.dumps(budget_amounts),
        'actual_amounts': json.dumps(actual_amounts),
        'current_month': today.strftime('%B %Y')
    }
    
    return render(request, 'dashboard/budget_performance.html', context)

@login_required
def dashboard_api_expense_breakdown(request):
    """API endpoint for expense breakdown data."""
    # Get current month
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    # Get user's expenses for current month
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start,
        date__lte=today
    )
    
    # Calculate total expenses
    current_month_total = sum(expense.amount for expense in current_month_expenses)
    
    # Get expense breakdown by category
    categories = ExpenseCategory.objects.all()
    expense_breakdown = []
    
    for category in categories:
        category_expenses = current_month_expenses.filter(category=category)
        category_total = sum(expense.amount for expense in category_expenses)
        
        if category_total > 0:
            expense_breakdown.append({
                'category': category.name,
                'amount': float(category_total),
                'percentage': float((category_total / current_month_total * 100) if current_month_total > 0 else 0)
            })
    
    # Sort by amount (descending)
    expense_breakdown = sorted(expense_breakdown, key=lambda x: x['amount'], reverse=True)
    
    return JsonResponse({'expense_breakdown': expense_breakdown})

@login_required
def dashboard_api_weekly_spending(request):
    """API endpoint for weekly spending trend data."""
    # Get current date
    today = timezone.now().date()
    
    # Get weekly spending trend (last 4 weeks)
    weekly_spending = []
    
    for i in range(4, 0, -1):
        week_end = today - timedelta(days=today.weekday() + 1 + (7 * (i - 1)))
        week_start = week_end - timedelta(days=6)
        
        week_expenses = Expense.objects.filter(
            user=request.user,
            date__gte=week_start,
            date__lte=week_end
        )
        
        week_total = sum(expense.amount for expense in week_expenses)
        
        weekly_spending.append({
            'week': f'Week {5-i}',
            'start_date': week_start.strftime('%m/%d'),
            'end_date': week_end.strftime('%m/%d'),
            'amount': float(week_total)
        })
    
    return JsonResponse({'weekly_spending': weekly_spending})

# Helper functions

def calculate_total_assets(user):
    """Calculate total assets for a user."""
    # Get user profile
    user_profile = UserProfile.objects.get(user=user)
    
    # Cash assets
    cash_assets = user_profile.cash_balance + user_profile.emergency_fund
    
    # Investment assets
    investments = Investment.objects.filter(
        user=user,
        status='active',
        is_simulation=False
    )
    investment_assets = sum(inv.current_value for inv in investments)
    
    # Other assets (property, vehicles, etc.)
    other_assets = user_profile.other_assets_value
    
    return cash_assets + investment_assets + other_assets

def calculate_total_liabilities(user):
    """Calculate total liabilities for a user."""
    # Get loans
    loans = Loan.objects.filter(
        user=user,
        status='active'
    )
    loan_liabilities = sum(loan.remaining_balance for loan in loans)
    
    # Get user profile for other liabilities
    user_profile = UserProfile.objects.get(user=user)
    other_liabilities = user_profile.other_liabilities_value
    
    return loan_liabilities + other_liabilities

def calculate_monthly_debt_payments(user):
    """Calculate total monthly debt payments for a user."""
    # Get loans
    loans = Loan.objects.filter(
        user=user,
        status='active'
    )
    loan_payments = sum(loan.monthly_payment for loan in loans)
    
    # Get user profile for other debt payments
    user_profile = UserProfile.objects.get(user=user)
    other_debt_payments = user_profile.other_monthly_debt_payments
    
    return loan_payments + other_debt_payments

def calculate_average_monthly_expenses(user):
    """Calculate average monthly expenses for a user (last 3 months)."""
    # Get current date
    today = timezone.now().date()
    three_months_ago = today - timedelta(days=90)
    
    # Get expenses for last 3 months
    expenses = Expense.objects.filter(
        user=user,
        date__gte=three_months_ago,
        date__lte=today
    )
    
    total_expenses = sum(expense.amount for expense in expenses)
    
    # Calculate monthly average
    return total_expenses / 3

def calculate_savings_rate(user):
    """Calculate savings rate for a user (last 3 months)."""
    # Get user profile
    user_profile = UserProfile.objects.get(user=user)
    monthly_income = user_profile.monthly_income
    
    # Get current date
    today = timezone.now().date()
    three_months_ago = today - timedelta(days=90)
    
    # Get expenses for last 3 months
    expenses = Expense.objects.filter(
        user=user,
        date__gte=three_months_ago,
        date__lte=today
    )
    
    total_expenses = sum(expense.amount for expense in expenses)
    
    # Calculate total income for 3 months
    total_income = monthly_income * 3
    
    # Calculate savings and savings rate
    if total_income > 0:
        savings = total_income - total_expenses
        savings_rate = (savings / total_income) * 100
    else:
        savings_rate = 0
    
    return savings_rate

def calculate_financial_health_score(debt_to_income, emergency_fund_months, savings_rate):
    """Calculate financial health score (0-100)."""
    # Debt-to-income score (lower is better)
    if debt_to_income <= 20:
        dti_score = 100
    elif debt_to_income <= 36:
        dti_score = 80
    elif debt_to_income <= 43:
        dti_score = 60
    elif debt_to_income <= 50:
        dti_score = 40
    else:
        dti_score = 20
    
    # Emergency fund score (higher is better)
    if emergency_fund_months >= 6:
        ef_score = 100
    elif emergency_fund_months >= 3:
        ef_score = 80
    elif emergency_fund_months >= 1:
        ef_score = 60
    elif emergency_fund_months > 0:
        ef_score = 40
    else:
        ef_score = 20
    
    # Savings rate score (higher is better)
    if savings_rate >= 20:
        sr_score = 100
    elif savings_rate >= 15:
        sr_score = 80
    elif savings_rate >= 10:
        sr_score = 60
    elif savings_rate >= 5:
        sr_score = 40
    else:
        sr_score = 20
    
    # Calculate weighted average
    return (dti_score * 0.4) + (ef_score * 0.3) + (sr_score * 0.3)
