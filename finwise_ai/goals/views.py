from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import SavingsGoal, GoalContribution, GoalMilestone
from .forms import SavingsGoalForm, GoalContributionForm, GoalMilestoneForm, SavingsPlanForm
import json
import numpy as np

@login_required
def goals_home(request):
    """View for the savings goals dashboard."""
    # Get user's active goals
    active_goals = SavingsGoal.objects.filter(
        user=request.user,
        status='active'
    ).order_by('target_date')
    
    # Get user's completed goals
    completed_goals = SavingsGoal.objects.filter(
        user=request.user,
        status='completed'
    ).order_by('-target_date')[:5]
    
    # Calculate total savings
    total_saved = sum(goal.current_amount for goal in active_goals)
    total_target = sum(goal.target_amount for goal in active_goals)
    
    # Calculate overall progress
    overall_progress = 0
    if total_target > 0:
        overall_progress = (total_saved / total_target) * 100
    
    # Get upcoming milestones
    today = timezone.now().date()
    next_month = today + timedelta(days=30)
    upcoming_milestones = GoalMilestone.objects.filter(
        goal__user=request.user,
        goal__status='active',
        target_date__gte=today,
        target_date__lte=next_month,
        is_reached=False
    ).order_by('target_date')
    
    # Get recent contributions
    recent_contributions = GoalContribution.objects.filter(
        goal__user=request.user
    ).order_by('-date')[:5]
    
    # Get all goals for template compatibility
    all_goals = SavingsGoal.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'goals': all_goals,  # For template compatibility
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'goals_count': all_goals.count(),
        'active_goals_count': active_goals.count(),
        'total_saved': total_saved,
        'total_target': total_target,
        'overall_progress': overall_progress,
        'upcoming_milestones': upcoming_milestones,
        'recent_contributions': recent_contributions,
    }
    
    return render(request, 'goals/goals_home.html', context)

@login_required
def goal_list(request):
    """View for listing all savings goals."""
    # Get all goals for the user
    goals = SavingsGoal.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'goals': goals,
    }
    
    return render(request, 'goals/goal_list.html', context)

@login_required
def goal_detail(request, pk):
    """View for displaying goal details."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    
    # Get contributions
    contributions = GoalContribution.objects.filter(goal=goal).order_by('-date')
    
    # Get milestones
    milestones = GoalMilestone.objects.filter(goal=goal).order_by('target_amount')
    
    # Calculate time remaining
    today = timezone.now().date()
    if today < goal.target_date:
        days_remaining = (goal.target_date - today).days
        months_remaining = days_remaining // 30
    else:
        days_remaining = 0
        months_remaining = 0
    
    # Calculate required monthly contribution to reach goal
    required_monthly = 0
    if months_remaining > 0:
        required_monthly = (goal.target_amount - goal.current_amount) / months_remaining
    
    # Calculate contribution history for chart
    contribution_history = []
    running_total = 0
    
    for contrib in contributions.order_by('date'):
        running_total += contrib.amount
        contribution_history.append({
            'date': contrib.date.strftime('%Y-%m-%d'),
            'amount': contrib.amount,
            'running_total': running_total
        })
    
    # Convert Decimal to float for JSON serialization
    contribution_history_json = []
    for item in contribution_history:
        contribution_history_json.append({
            'amount': float(item['amount']),
            'date': item['date'],
            'running_total': float(item['running_total'])
        })
    
    context = {
        'goal': goal,
        'contributions': contributions,
        'milestones': milestones,
        'days_remaining': days_remaining,
        'months_remaining': months_remaining,
        'required_monthly': required_monthly,
        'contribution_history': json.dumps(contribution_history_json),
    }
    
    return render(request, 'goals/goal_detail.html', context)

@login_required
def goal_create(request):
    """View for creating a new savings goal."""
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.current_amount = 0
            goal.save()
            
            messages.success(request, 'Savings goal created successfully!')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        form = SavingsGoalForm()
    
    context = {
        'form': form,
        'title': 'Create Savings Goal',
    }
    
    return render(request, 'goals/goal_form.html', context)

@login_required
def goal_edit(request, pk):
    """View for editing an existing savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Savings goal updated successfully!')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        form = SavingsGoalForm(instance=goal)
    
    context = {
        'form': form,
        'goal': goal,
        'title': 'Edit Savings Goal',
    }
    
    return render(request, 'goals/goal_form.html', context)

@login_required
def goal_delete(request, pk):
    """View for deleting a savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete associated contributions and milestones
        GoalContribution.objects.filter(goal=goal).delete()
        GoalMilestone.objects.filter(goal=goal).delete()
        
        goal.delete()
        messages.success(request, 'Savings goal deleted successfully!')
        return redirect('goals:goal_list')
    
    context = {
        'goal': goal,
    }
    
    return render(request, 'goals/goal_confirm_delete.html', context)

@login_required
def contribution_add(request, goal_id):
    """View for adding a contribution to a savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=goal_id, user=request.user)
    
    if request.method == 'POST':
        form = GoalContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.save()
            
            # Update goal's current amount
            goal.current_amount += contribution.amount
            
            # Check if goal is completed
            if goal.current_amount >= goal.target_amount:
                goal.status = 'completed'
                messages.success(request, 'Congratulations! You have reached your savings goal!')
            
            goal.save()
            
            # Check if any milestones are reached
            check_milestones(goal)
            
            messages.success(request, 'Contribution added successfully!')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        form = GoalContributionForm(initial={'date': timezone.now().date()})
    
    context = {
        'form': form,
        'goal': goal,
    }
    
    return render(request, 'goals/contribution_form.html', context)

@login_required
def contribution_delete(request, pk):
    """View for deleting a contribution."""
    contribution = get_object_or_404(GoalContribution, pk=pk, goal__user=request.user)
    goal = contribution.goal
    
    if request.method == 'POST':
        # Update goal's current amount
        goal.current_amount -= contribution.amount
        goal.save()
        
        contribution.delete()
        messages.success(request, 'Contribution deleted successfully!')
        return redirect('goals:goal_detail', pk=goal.pk)
    
    context = {
        'contribution': contribution,
        'goal': goal,
    }
    
    return render(request, 'goals/contribution_confirm_delete.html', context)

@login_required
def milestone_add(request, goal_id):
    """View for adding a milestone to a savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=goal_id, user=request.user)
    
    if request.method == 'POST':
        form = GoalMilestoneForm(request.POST, goal=goal)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.goal = goal
            
            # Check if milestone is already reached
            if goal.current_amount >= milestone.target_amount:
                milestone.is_reached = True
                milestone.reached_date = timezone.now().date()
            
            milestone.save()
            messages.success(request, 'Milestone added successfully!')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        form = GoalMilestoneForm(goal=goal)
    
    context = {
        'form': form,
        'goal': goal,
    }
    
    return render(request, 'goals/milestone_form.html', context)

@login_required
def milestone_edit(request, pk):
    """View for editing a milestone."""
    milestone = get_object_or_404(GoalMilestone, pk=pk, goal__user=request.user)
    goal = milestone.goal
    
    if request.method == 'POST':
        form = GoalMilestoneForm(request.POST, instance=milestone, goal=goal)
        if form.is_valid():
            milestone = form.save()
            
            # Check if milestone is reached
            if goal.current_amount >= milestone.target_amount and not milestone.is_reached:
                milestone.is_reached = True
                milestone.reached_date = timezone.now().date()
                milestone.save()
            
            messages.success(request, 'Milestone updated successfully!')
            return redirect('goals:goal_detail', pk=goal.pk)
    else:
        form = GoalMilestoneForm(instance=milestone, goal=goal)
    
    context = {
        'form': form,
        'milestone': milestone,
        'goal': goal,
    }
    
    return render(request, 'goals/milestone_form.html', context)

@login_required
def milestone_delete(request, pk):
    """View for deleting a milestone."""
    milestone = get_object_or_404(GoalMilestone, pk=pk, goal__user=request.user)
    goal = milestone.goal
    
    if request.method == 'POST':
        milestone.delete()
        messages.success(request, 'Milestone deleted successfully!')
        return redirect('goals:goal_detail', pk=goal.pk)
    
    context = {
        'milestone': milestone,
        'goal': goal,
    }
    
    return render(request, 'goals/milestone_confirm_delete.html', context)

@login_required
def savings_plan(request):
    """View for generating a savings plan."""
    if request.method == 'POST':
        form = SavingsPlanForm(request.POST)
        if form.is_valid():
            # Get form data
            current_savings = form.cleaned_data['current_savings']
            target_amount = form.cleaned_data['target_amount']
            target_date = form.cleaned_data['target_date']
            monthly_income = form.cleaned_data['monthly_income']
            monthly_expenses = form.cleaned_data['monthly_expenses']
            risk_tolerance = form.cleaned_data['risk_tolerance']
            
            # Calculate time frame
            today = timezone.now().date()
            months_remaining = ((target_date.year - today.year) * 12) + (target_date.month - today.month)
            
            # Calculate amount needed
            amount_needed = target_amount - current_savings
            
            # Calculate monthly disposable income
            disposable_income = monthly_income - monthly_expenses
            
            # Calculate required monthly savings
            required_monthly = amount_needed / months_remaining if months_remaining > 0 else amount_needed
            
            # Check if plan is feasible
            is_feasible = required_monthly <= disposable_income
            
            # Generate savings plan
            savings_plan = generate_savings_plan(
                current_savings, target_amount, months_remaining, 
                disposable_income, risk_tolerance
            )
            
            context = {
                'form': form,
                'current_savings': current_savings,
                'target_amount': target_amount,
                'target_date': target_date,
                'months_remaining': months_remaining,
                'amount_needed': amount_needed,
                'disposable_income': disposable_income,
                'required_monthly': required_monthly,
                'is_feasible': is_feasible,
                'savings_plan': savings_plan,
                'risk_tolerance': risk_tolerance,
            }
            
            return render(request, 'goals/savings_plan_result.html', context)
    else:
        form = SavingsPlanForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'goals/savings_plan_form.html', context)

@login_required
def goal_progress_chart(request, pk):
    """API view for goal progress chart data."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    
    # Get contributions
    contributions = GoalContribution.objects.filter(goal=goal).order_by('date')
    
    # Calculate contribution history
    contribution_history = []
    running_total = 0
    
    for contrib in contributions:
        running_total += contrib.amount
        contribution_history.append({
            'date': contrib.date.strftime('%Y-%m-%d'),
            'amount': float(contrib.amount),
            'running_total': float(running_total)
        })
    
    # Calculate target line
    if goal.start_date and goal.target_date:
        days_total = (goal.target_date - goal.start_date).days
        if days_total > 0:
            daily_target = goal.target_amount / days_total
            
            target_line = []
            current_date = goal.start_date
            current_target = 0
            
            while current_date <= goal.target_date:
                current_target += daily_target
                target_line.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'target': float(min(current_target, goal.target_amount))
                })
                current_date += timedelta(days=1)
        else:
            target_line = [{
                'date': goal.start_date.strftime('%Y-%m-%d'),
                'target': float(goal.target_amount)
            }]
    else:
        target_line = []
    
    data = {
        'contribution_history': contribution_history,
        'target_line': target_line,
        'current_amount': float(goal.current_amount),
        'target_amount': float(goal.target_amount),
        'progress_percentage': float(goal.progress_percentage),
    }
    
    return JsonResponse(data)

# Helper functions

def check_milestones(goal):
    """Check if any milestones are reached for a goal."""
    milestones = GoalMilestone.objects.filter(
        goal=goal,
        is_reached=False,
        target_amount__lte=goal.current_amount
    )
    
    for milestone in milestones:
        milestone.is_reached = True
        milestone.reached_date = timezone.now().date()
        milestone.save()

def generate_savings_plan(current_savings, target_amount, months_remaining, disposable_income, risk_tolerance):
    """Generate a savings plan based on user inputs."""
    amount_needed = target_amount - current_savings
    
    # Calculate required monthly savings
    required_monthly = amount_needed / months_remaining if months_remaining > 0 else amount_needed
    
    # Adjust based on risk tolerance
    if risk_tolerance == 'low':
        # Conservative approach - steady monthly savings
        monthly_contribution = min(required_monthly, disposable_income)
        expected_return_rate = 0.03  # 3% annual return
    elif risk_tolerance == 'medium':
        # Balanced approach - slightly higher monthly contribution
        monthly_contribution = min(required_monthly * 1.1, disposable_income)
        expected_return_rate = 0.06  # 6% annual return
    else:  # high
        # Aggressive approach - higher monthly contribution
        monthly_contribution = min(required_monthly * 1.2, disposable_income)
        expected_return_rate = 0.09  # 9% annual return
    
    # Generate monthly projection
    monthly_projection = []
    running_total = current_savings
    monthly_return_rate = expected_return_rate / 12
    
    for month in range(1, months_remaining + 1):
        # Calculate interest/returns for this month
        monthly_return = running_total * monthly_return_rate
        
        # Add contribution
        running_total += monthly_contribution + monthly_return
        
        monthly_projection.append({
            'month': month,
            'contribution': monthly_contribution,
            'returns': monthly_return,
            'balance': running_total,
            'target_progress': (running_total / target_amount) * 100
        })
    
    # Calculate final projections
    final_balance = running_total
    total_contributions = monthly_contribution * months_remaining
    total_returns = final_balance - current_savings - total_contributions
    
    return {
        'monthly_contribution': monthly_contribution,
        'expected_return_rate': expected_return_rate * 100,  # Convert to percentage
        'monthly_projection': monthly_projection,
        'final_balance': final_balance,
        'total_contributions': total_contributions,
        'total_returns': total_returns,
        'will_reach_target': final_balance >= target_amount,
        'months_to_target': next((m['month'] for m in monthly_projection if m['balance'] >= target_amount), months_remaining)
    }
