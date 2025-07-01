from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import InvestmentType, Investment, InvestmentSimulation, InvestmentTransaction
from .forms import InvestmentTypeForm, InvestmentForm, InvestmentTransactionForm, InvestmentSimulationForm
import json
import numpy as np
import pandas as pd

@login_required
def investments_home(request):
    """View for the investments dashboard."""
    # Get user's active investments
    active_investments = Investment.objects.filter(
        user=request.user,
        status='active',
        is_simulation=False
    ).order_by('-purchase_date')
    
    # Get user's simulated investments
    simulated_investments = Investment.objects.filter(
        user=request.user,
        is_simulation=True
    ).order_by('-created_at')[:5]
    
    # Calculate total portfolio value
    total_value = sum(inv.current_value for inv in active_investments)
    total_cost = sum(inv.purchase_price * inv.quantity for inv in active_investments)
    
    # Calculate total return
    total_return = total_value - total_cost
    total_return_percentage = (total_return / total_cost * 100) if total_cost > 0 else 0
    
    # Get portfolio breakdown by category
    portfolio_breakdown = []
    categories = InvestmentType.CATEGORY_CHOICES
    
    for category_code, category_name in categories:
        category_investments = active_investments.filter(investment_type__category=category_code)
        category_value = sum(inv.current_value for inv in category_investments)
        
        if category_value > 0:
            portfolio_breakdown.append({
                'category': category_name,
                'value': category_value,
                'percentage': (category_value / total_value * 100) if total_value > 0 else 0
            })
    
    # Get recent transactions
    recent_transactions = InvestmentTransaction.objects.filter(
        investment__user=request.user
    ).order_by('-date')[:5]
    
    context = {
        'active_investments': active_investments,
        'simulated_investments': simulated_investments,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_return': total_return,
        'total_return_percentage': total_return_percentage,
        'portfolio_breakdown': portfolio_breakdown,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'investments/investments_home.html', context)

@login_required
def investment_list(request):
    """View for listing all investments."""
    # Get all investments for the user
    investments = Investment.objects.filter(
        user=request.user,
        is_simulation=False
    ).order_by('-purchase_date')
    
    context = {
        'investments': investments,
    }
    
    return render(request, 'investments/investment_list.html', context)

@login_required
def investment_detail(request, pk):
    """View for displaying investment details."""
    investment = get_object_or_404(Investment, pk=pk, user=request.user)
    
    # Get transactions
    transactions = InvestmentTransaction.objects.filter(investment=investment).order_by('-date')
    
    # Calculate performance metrics
    cost_basis = investment.purchase_price * investment.quantity
    current_value = investment.current_value
    total_return = current_value - cost_basis
    return_percentage = (total_return / cost_basis * 100) if cost_basis > 0 else 0
    
    # Calculate holding period
    today = timezone.now().date()
    holding_period_days = (today - investment.purchase_date).days
    holding_period_years = holding_period_days / 365.25
    
    # Calculate annualized return
    if holding_period_years > 0:
        annualized_return = ((1 + (return_percentage / 100)) ** (1 / holding_period_years) - 1) * 100
    else:
        annualized_return = 0
    
    context = {
        'investment': investment,
        'transactions': transactions,
        'cost_basis': cost_basis,
        'current_value': current_value,
        'total_return': total_return,
        'return_percentage': return_percentage,
        'holding_period_days': holding_period_days,
        'holding_period_years': holding_period_years,
        'annualized_return': annualized_return,
    }
    
    return render(request, 'investments/investment_detail.html', context)

@login_required
def investment_create(request):
    """View for creating a new investment."""
    if request.method == 'POST':
        form = InvestmentForm(request.POST, user=request.user)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.user = request.user
            
            # Calculate current value for new investments
            investment.current_value = investment.purchase_price * investment.quantity
            
            investment.save()
            messages.success(request, 'Investment created successfully!')
            return redirect('investments:investment_detail', pk=investment.pk)
    else:
        form = InvestmentForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Add Investment',
    }
    
    return render(request, 'investments/investment_form.html', context)

@login_required
def investment_edit(request, pk):
    """View for editing an existing investment."""
    investment = get_object_or_404(Investment, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = InvestmentForm(request.POST, instance=investment, user=request.user)
        if form.is_valid():
            investment = form.save()
            messages.success(request, 'Investment updated successfully!')
            return redirect('investment_detail', pk=investment.pk)
    else:
        form = InvestmentForm(instance=investment, user=request.user)
    
    context = {
        'form': form,
        'investment': investment,
        'title': 'Edit Investment',
    }
    
    return render(request, 'investments/investment_form.html', context)

@login_required
def investment_delete(request, pk):
    """View for deleting an investment."""
    investment = get_object_or_404(Investment, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete associated transactions
        InvestmentTransaction.objects.filter(investment=investment).delete()
        
        investment.delete()
        messages.success(request, 'Investment deleted successfully!')
        return redirect('investments:investment_list')
    
    context = {
        'investment': investment,
    }
    
    return render(request, 'investments/investment_confirm_delete.html', context)

@login_required
def transaction_add(request, investment_id):
    """View for adding a transaction to an investment."""
    investment = get_object_or_404(Investment, pk=investment_id, user=request.user)
    
    if request.method == 'POST':
        form = InvestmentTransactionForm(request.POST)
        if form.is_valid():
            transaction_type = form.cleaned_data['transaction_type']
            date = form.cleaned_data['date']
            price = form.cleaned_data['price']
            quantity = form.cleaned_data['quantity']
            fees = form.cleaned_data.get('fees') or 0
            notes = form.cleaned_data.get('notes') or ''
            
            # Create transaction
            transaction = InvestmentTransaction.objects.create(
                investment=investment,
                transaction_type=transaction_type,
                date=date,
                price=price,
                quantity=quantity,
                fees=fees,
                notes=notes
            )
            
            # Update investment based on transaction type
            if transaction_type == 'buy':
                # Calculate new average purchase price
                total_quantity = investment.quantity + quantity
                total_cost = (investment.purchase_price * investment.quantity) + (price * quantity) + fees
                
                if total_quantity > 0:
                    investment.purchase_price = total_cost / total_quantity
                
                investment.quantity += quantity
                
            elif transaction_type == 'sell':
                investment.quantity -= quantity
                
                # If all shares are sold, mark as inactive
                if investment.quantity <= 0:
                    investment.status = 'inactive'
                    investment.quantity = 0
                
            elif transaction_type == 'dividend':
                # Dividends don't affect quantity, just record them
                pass
                
            elif transaction_type == 'split':
                # For stock splits, adjust quantity and price
                investment.quantity = investment.quantity * quantity
                investment.purchase_price = investment.purchase_price / quantity
            
            # Update current value
            investment.current_value = investment.quantity * price
            investment.save()
            
            messages.success(request, 'Transaction added successfully!')
            return redirect('investment_detail', pk=investment.pk)
    else:
        form = InvestmentTransactionForm(initial={'date': timezone.now().date()})
    
    context = {
        'form': form,
        'investment': investment,
    }
    
    return render(request, 'investments/transaction_form.html', context)

@login_required
def transaction_delete(request, pk):
    """View for deleting a transaction."""
    transaction = get_object_or_404(InvestmentTransaction, pk=pk, investment__user=request.user)
    investment = transaction.investment
    
    if request.method == 'POST':
        # Revert the effects of this transaction
        if transaction.transaction_type == 'buy':
            investment.quantity -= transaction.quantity
            
            # Recalculate average purchase price (simplified approach)
            other_buys = InvestmentTransaction.objects.filter(
                investment=investment,
                transaction_type='buy'
            ).exclude(pk=transaction.pk)
            
            if other_buys.exists():
                total_cost = sum(t.price * t.quantity + t.fees for t in other_buys)
                total_quantity = sum(t.quantity for t in other_buys)
                
                if total_quantity > 0:
                    investment.purchase_price = total_cost / total_quantity
            
        elif transaction.transaction_type == 'sell':
            investment.quantity += transaction.quantity
            
            # If status was inactive, reactivate
            if investment.status == 'inactive' and investment.quantity > 0:
                investment.status = 'active'
                
        elif transaction.transaction_type == 'split':
            # Reverse the split
            investment.quantity = investment.quantity / transaction.quantity
            investment.purchase_price = investment.purchase_price * transaction.quantity
        
        # Update current value
        investment.current_value = investment.quantity * transaction.price
        investment.save()
        
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('investment_detail', pk=investment.pk)
    
    context = {
        'transaction': transaction,
        'investment': investment,
    }
    
    return render(request, 'investments/transaction_confirm_delete.html', context)

@login_required
def investment_type_list(request):
    """View for listing investment types."""
    investment_types = InvestmentType.objects.all()
    
    context = {
        'investment_types': investment_types,
    }
    
    return render(request, 'investments/investment_type_list.html', context)

@login_required
def investment_type_create(request):
    """View for creating a new investment type."""
    if request.method == 'POST':
        form = InvestmentTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Investment type created successfully!')
            return redirect('investment_type_list')
    else:
        form = InvestmentTypeForm()
    
    context = {
        'form': form,
        'title': 'Add Investment Type',
    }
    
    return render(request, 'investments/investment_type_form.html', context)

@login_required
def investment_simulator(request):
    """View for simulating investments."""
    if request.method == 'POST':
        form = InvestmentSimulationForm(request.POST)
        if form.is_valid():
            simulation = form.save(commit=False)
            simulation.user = request.user
            simulation.save()
            
            # Run the simulation
            run_investment_simulation(simulation)
            
            return redirect('investment_simulation_result', pk=simulation.pk)
    else:
        form = InvestmentSimulationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'investments/investment_simulator.html', context)

@login_required
def investment_simulation_result(request, pk):
    """View for displaying investment simulation results."""
    simulation = get_object_or_404(InvestmentSimulation, pk=pk, user=request.user)
    
    # Get simulation data
    simulation_data = json.loads(simulation.simulation_data)
    
    # Calculate key metrics
    final_value = simulation_data[-1]['value']
    total_invested = simulation.initial_amount + (simulation.periodic_amount * (simulation.duration_years * 12 / simulation.period_months))
    total_return = final_value - total_invested
    return_percentage = (total_return / total_invested * 100) if total_invested > 0 else 0
    annualized_return = ((final_value / total_invested) ** (1 / simulation.duration_years) - 1) * 100 if simulation.duration_years > 0 and total_invested > 0 else 0
    
    context = {
        'simulation': simulation,
        'simulation_data': json.dumps(simulation_data),
        'final_value': final_value,
        'total_invested': total_invested,
        'total_return': total_return,
        'return_percentage': return_percentage,
        'annualized_return': annualized_return,
    }
    
    return render(request, 'investments/investment_simulation_result.html', context)

@login_required
def compare_strategies(request):
    """View for comparing investment strategies."""
    if request.method == 'POST':
        # Get form data
        investment_type = request.POST.get('investment_type')
        initial_amount = float(request.POST.get('initial_amount', 0))
        monthly_amount = float(request.POST.get('monthly_amount', 0))
        duration_years = int(request.POST.get('duration_years', 5))
        expected_return = float(request.POST.get('expected_return', 7))
        volatility = float(request.POST.get('volatility', 15))
        
        # Run simulations for different strategies
        lump_sum_data = simulate_strategy(
            'lump_sum',
            initial_amount + (monthly_amount * duration_years * 12),
            0,
            duration_years,
            expected_return,
            volatility
        )
        
        dca_data = simulate_strategy(
            'dca',
            initial_amount,
            monthly_amount,
            duration_years,
            expected_return,
            volatility
        )
        
        value_averaging_data = simulate_strategy(
            'value_averaging',
            initial_amount,
            monthly_amount,
            duration_years,
            expected_return,
            volatility
        )
        
        # Calculate final values
        lump_sum_final = lump_sum_data[-1]['value']
        dca_final = dca_data[-1]['value']
        value_averaging_final = value_averaging_data[-1]['value']
        
        # Calculate total invested
        lump_sum_invested = initial_amount + (monthly_amount * duration_years * 12)
        dca_invested = initial_amount + (monthly_amount * duration_years * 12)
        value_averaging_invested = initial_amount + sum(point.get('contribution', 0) for point in value_averaging_data)
        
        context = {
            'investment_type': investment_type,
            'initial_amount': initial_amount,
            'monthly_amount': monthly_amount,
            'duration_years': duration_years,
            'expected_return': expected_return,
            'volatility': volatility,
            'lump_sum_data': json.dumps(lump_sum_data),
            'dca_data': json.dumps(dca_data),
            'value_averaging_data': json.dumps(value_averaging_data),
            'lump_sum_final': lump_sum_final,
            'dca_final': dca_final,
            'value_averaging_final': value_averaging_final,
            'lump_sum_invested': lump_sum_invested,
            'dca_invested': dca_invested,
            'value_averaging_invested': value_averaging_invested,
        }
        
        return render(request, 'investments/compare_strategies_result.html', context)
    
    # Get investment types for the form
    investment_types = InvestmentType.objects.all()
    
    context = {
        'investment_types': investment_types,
    }
    
    return render(request, 'investments/compare_strategies_form.html', context)

@login_required
def portfolio_analysis(request):
    """View for analyzing the user's investment portfolio."""
    # Get user's active investments
    investments = Investment.objects.filter(
        user=request.user,
        status='active',
        is_simulation=False
    )
    
    if not investments.exists():
        messages.info(request, 'You need to add investments to your portfolio before analyzing it.')
        return redirect('investments:investment_list')
    
    # Calculate portfolio metrics
    total_value = sum(inv.current_value for inv in investments)
    total_cost = sum(inv.purchase_price * inv.quantity for inv in investments)
    
    # Calculate allocation by category
    allocation = {}
    for inv in investments:
        category = inv.investment_type.get_category_display()
        if category not in allocation:
            allocation[category] = 0
        allocation[category] += inv.current_value
    
    # Convert to percentages
    allocation_percentages = {k: (v / total_value * 100) for k, v in allocation.items()}
    
    # Calculate risk metrics
    # (In a real app, this would use historical data and more sophisticated calculations)
    avg_risk = sum(inv.investment_type.risk_level for inv in investments) / len(investments)
    
    # Calculate performance metrics
    total_return = total_value - total_cost
    return_percentage = (total_return / total_cost * 100) if total_cost > 0 else 0
    
    context = {
        'investments': investments,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_return': total_return,
        'return_percentage': return_percentage,
        'allocation': allocation,
        'allocation_percentages': allocation_percentages,
        'avg_risk': avg_risk,
    }
    
    return render(request, 'investments/portfolio_analysis.html', context)

# Helper functions

def run_investment_simulation(simulation):
    """Run an investment simulation and store the results."""
    # Get simulation parameters
    initial_amount = simulation.initial_amount
    periodic_amount = simulation.periodic_amount
    period_months = simulation.period_months
    duration_years = simulation.duration_years
    expected_return = simulation.expected_return
    volatility = simulation.volatility
    strategy = simulation.strategy
    
    # Run the appropriate simulation
    simulation_data = simulate_strategy(
        strategy,
        initial_amount,
        periodic_amount,
        duration_years,
        expected_return,
        volatility,
        period_months
    )
    
    # Store simulation results
    simulation.simulation_data = json.dumps(simulation_data)
    simulation.save()

def simulate_strategy(strategy, initial_amount, periodic_amount, duration_years, expected_return, volatility, period_months=1):
    """Simulate an investment strategy and return the results."""
    # Convert annual return to monthly
    monthly_return = (1 + expected_return / 100) ** (1/12) - 1
    monthly_volatility = volatility / 100 / np.sqrt(12)
    
    # Calculate number of periods
    num_periods = int(duration_years * 12 / period_months)
    
    # Initialize simulation data
    simulation_data = []
    current_value = initial_amount
    total_invested = initial_amount
    
    # Run simulation
    for period in range(num_periods + 1):
        if period == 0:
            # Initial state
            simulation_data.append({
                'period': period,
                'value': current_value,
                'invested': total_invested,
                'return': 0
            })
            continue
        
        # Calculate return for this period
        if strategy == 'lump_sum':
            # Lump sum: all money invested at the beginning
            contribution = 0 if period > 1 else 0  # No additional contributions
            
        elif strategy == 'dca':
            # Dollar cost averaging: regular contributions
            contribution = periodic_amount
            
        elif strategy == 'value_averaging':
            # Value averaging: adjust contributions to reach target value
            target_value = initial_amount + (period * periodic_amount)
            contribution = max(0, target_value - current_value)
        
        # Add contribution
        current_value += contribution
        total_invested += contribution
        
        # Calculate return with randomness
        period_return = np.random.normal(monthly_return, monthly_volatility) * current_value
        current_value += period_return
        
        # Ensure value doesn't go negative
        current_value = max(0, current_value)
        
        # Store data point
        simulation_data.append({
            'period': period,
            'value': current_value,
            'contribution': contribution,
            'return': period_return,
            'invested': total_invested
        })
    
    return simulation_data

def calculate_interest_rate(investment_type, credit_score, employment_years):
    """Calculate interest rate based on investment type, credit score, and employment history."""
    # Base rate from investment type
    base_rate = investment_type.avg_annual_return
    
    # Adjust for credit score
    if credit_score >= 800:
        credit_adjustment = -1.0
    elif credit_score >= 750:
        credit_adjustment = -0.5
    elif credit_score >= 700:
        credit_adjustment = 0
    elif credit_score >= 650:
        credit_adjustment = 0.5
    elif credit_score >= 600:
        credit_adjustment = 1.5
    else:
        credit_adjustment = 3.0
    
    # Adjust for employment history
    if employment_years >= 5:
        employment_adjustment = -0.25
    elif employment_years >= 2:
        employment_adjustment = 0
    else:
        employment_adjustment = 0.25
    
    # Calculate final rate
    final_rate = base_rate + credit_adjustment + employment_adjustment
    
    # Ensure rate is within reasonable bounds
    return max(2.0, min(final_rate, 18.0))
