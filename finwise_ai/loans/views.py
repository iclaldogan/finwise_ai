from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Loan, LoanType, LoanPayment, LoanEligibility
from .forms import LoanForm, LoanTypeForm, LoanSimulatorForm, LoanEligibilityForm
import json
import numpy as np

@login_required
def loan_home(request):
    """View for the loans dashboard."""
    # Get user's active loans
    active_loans = Loan.objects.filter(
        user=request.user,
        status='active'
    ).order_by('end_date')
    
    # Get user's simulated loans
    simulated_loans = Loan.objects.filter(
        user=request.user,
        is_simulation=True
    ).order_by('-created_at')[:5]
    
    # Calculate total debt
    total_debt = active_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0
    
    # Calculate monthly payments
    monthly_payments = active_loans.aggregate(total=Sum('monthly_payment'))['total'] or 0
    
    # Get upcoming payments
    today = timezone.now().date()
    next_month = today + timedelta(days=30)
    upcoming_payments = LoanPayment.objects.filter(
        loan__user=request.user,
        payment_date__gte=today,
        payment_date__lte=next_month,
        is_paid=False
    ).order_by('payment_date')
    
    context = {
        'active_loans': active_loans,
        'simulated_loans': simulated_loans,
        'total_debt': total_debt,
        'monthly_payments': monthly_payments,
        'upcoming_payments': upcoming_payments,
    }
    
    return render(request, 'loans/loans_home.html', context)

@login_required
def loan_list(request):
    """View for listing all loans."""
    # Get all loans for the user
    loans = Loan.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'loans': loans,
    }
    
    return render(request, 'loans/loan_list.html', context)

@login_required
def loan_detail(request, pk):
    """View for displaying loan details."""
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    
    # Get loan payments
    payments = LoanPayment.objects.filter(loan=loan).order_by('payment_date')
    
    # Calculate amortization schedule
    amortization_schedule = []
    
    if not loan.is_simulation and loan.status == 'active':
        # Calculate remaining payments
        remaining_payments = payments.filter(payment_date__gte=timezone.now().date())
        
        # Calculate total interest to be paid
        total_interest = sum(payment.interest_amount for payment in remaining_payments)
        
        # Calculate total principal to be paid
        total_principal = sum(payment.principal_amount for payment in remaining_payments)
    else:
        # For simulations, calculate theoretical amortization schedule
        principal = loan.amount
        rate = loan.interest_rate / 100 / 12  # Monthly interest rate
        term = loan.term_months
        
        # Calculate monthly payment using the formula: P = (r * PV) / (1 - (1 + r)^-n)
        monthly_payment = (rate * principal) / (1 - (1 + rate) ** -term)
        
        # Generate amortization schedule
        balance = principal
        total_interest = 0
        
        for month in range(1, term + 1):
            interest_payment = balance * rate
            principal_payment = monthly_payment - interest_payment
            balance -= principal_payment
            
            amortization_schedule.append({
                'month': month,
                'payment': monthly_payment,
                'principal': principal_payment,
                'interest': interest_payment,
                'balance': max(0, balance)
            })
            
            total_interest += interest_payment
        
        total_principal = principal
    
    context = {
        'loan': loan,
        'payments': payments,
        'amortization_schedule': amortization_schedule,
        'total_interest': total_interest,
        'total_principal': total_principal,
        'total_cost': total_interest + total_principal,
    }
    
    return render(request, 'loans/loan_detail.html', context)

@login_required
def loan_create(request):
    """View for creating a new loan."""
    if request.method == 'POST':
        form = LoanForm(request.POST, user=request.user)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.user = request.user
            
            # Calculate end date if not provided
            if not loan.end_date and loan.start_date:
                loan.end_date = loan.start_date + relativedelta(months=loan.term_months)
            
            # Calculate remaining balance for new loans
            if loan.status == 'active':
                loan.remaining_balance = loan.amount
            
            loan.save()
            
            # Generate payment schedule for active loans
            if loan.status == 'active' and not loan.is_simulation:
                generate_payment_schedule(loan)
            
            messages.success(request, 'Loan created successfully!')
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = LoanForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Add Loan',
    }
    
    return render(request, 'loans/loan_form.html', context)

@login_required
def loan_edit(request, pk):
    """View for editing an existing loan."""
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = LoanForm(request.POST, instance=loan, user=request.user)
        if form.is_valid():
            loan = form.save()
            
            # Recalculate payment schedule if needed
            if loan.status == 'active' and not loan.is_simulation:
                # Delete future unpaid payments
                LoanPayment.objects.filter(
                    loan=loan,
                    payment_date__gt=timezone.now().date(),
                    is_paid=False
                ).delete()
                
                # Regenerate payment schedule
                generate_payment_schedule(loan)
            
            messages.success(request, 'Loan updated successfully!')
            return redirect('loans:loan_detail', pk=loan.pk)
    else:
        form = LoanForm(instance=loan, user=request.user)
    
    context = {
        'form': form,
        'loan': loan,
        'title': 'Edit Loan',
    }
    
    return render(request, 'loans/loan_form.html', context)

@login_required
def loan_delete(request, pk):
    """View for deleting a loan."""
    loan = get_object_or_404(Loan, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete associated payments
        LoanPayment.objects.filter(loan=loan).delete()
        
        loan.delete()
        messages.success(request, 'Loan deleted successfully!')
        return redirect('loans:loan_list')
    
    context = {
        'loan': loan,
    }
    
    return render(request, 'loans/loan_confirm_delete.html', context)

@login_required
def loan_simulator(request):
    """View for simulating loans."""
    if request.method == 'POST':
        form = LoanSimulatorForm(request.POST)
        if form.is_valid():
            # Get form data
            loan_type = form.cleaned_data['loan_type']
            amount = form.cleaned_data['amount']
            interest_rate = form.cleaned_data['interest_rate']
            term_years = form.cleaned_data['term_years']
            monthly_income = form.cleaned_data['monthly_income']
            existing_debt = form.cleaned_data.get('existing_debt') or 0
            
            # Calculate monthly payment
            term_months = term_years * 12
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = (monthly_rate * amount) / (1 - (1 + monthly_rate) ** -term_months)
            
            # Calculate debt-to-income ratio
            dti_ratio = ((monthly_payment + existing_debt) / monthly_income) * 100
            
            # Determine eligibility
            is_eligible = dti_ratio <= 43  # Standard DTI threshold
            
            # Create a simulated loan
            loan = Loan.objects.create(
                user=request.user,
                loan_type=LoanType.objects.get_or_create(name=loan_type.capitalize())[0],
                amount=amount,
                interest_rate=interest_rate,
                term_months=term_months,
                monthly_payment=monthly_payment,
                status='simulated',
                is_simulation=True
            )
            
            # Create eligibility record
            eligibility = LoanEligibility.objects.create(
                user=request.user,
                loan_type=loan.loan_type,
                requested_amount=amount,
                requested_term_months=term_months,
                is_eligible=is_eligible,
                max_eligible_amount=amount if is_eligible else calculate_max_eligible_amount(monthly_income, existing_debt, interest_rate, term_months),
                offered_interest_rate=interest_rate,
                reason="Debt-to-income ratio is {:.1f}%. {}".format(
                    dti_ratio,
                    "This is within acceptable limits." if is_eligible else "This exceeds our maximum threshold of 43%."
                )
            )
            
            return redirect('loans:loan_simulation_result', loan_id=loan.pk, eligibility_id=eligibility.pk)
    else:
        form = LoanSimulatorForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'loans/loan_simulator.html', context)

@login_required
def loan_simulation_result(request, loan_id, eligibility_id):
    """View for displaying loan simulation results."""
    loan = get_object_or_404(Loan, pk=loan_id, user=request.user, is_simulation=True)
    eligibility = get_object_or_404(LoanEligibility, pk=eligibility_id, user=request.user)
    
    # Calculate amortization schedule
    principal = loan.amount
    rate = loan.interest_rate / 100 / 12  # Monthly interest rate
    term = loan.term_months
    monthly_payment = loan.monthly_payment
    
    # Generate amortization schedule
    amortization_schedule = []
    balance = principal
    total_interest = 0
    
    for month in range(1, term + 1):
        interest_payment = balance * rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        
        amortization_schedule.append({
            'month': month,
            'payment': monthly_payment,
            'principal': principal_payment,
            'interest': interest_payment,
            'balance': max(0, balance)
        })
        
        total_interest += interest_payment
    
    context = {
        'loan': loan,
        'eligibility': eligibility,
        'amortization_schedule': amortization_schedule,
        'total_interest': total_interest,
        'total_cost': total_interest + principal,
        'monthly_payment': monthly_payment,
    }
    
    return render(request, 'loans/loan_simulation_result.html', context)

@login_required
def loan_payment_mark_paid(request, pk):
    """View for marking a loan payment as paid."""
    payment = get_object_or_404(LoanPayment, pk=pk, loan__user=request.user)
    
    if request.method == 'POST':
        payment.is_paid = True
        payment.save()
        
        # Update loan remaining balance
        loan = payment.loan
        loan.remaining_balance -= payment.principal_amount
        loan.save()
        
        # Check if loan is paid off
        if loan.remaining_balance <= 0:
            loan.status = 'paid'
            loan.save()
            messages.success(request, 'Congratulations! This loan has been fully paid off.')
        else:
            messages.success(request, 'Payment marked as paid successfully!')
        
        return redirect('loans:loan_detail', pk=payment.loan.pk)
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'loans/payment_confirm_paid.html', context)

@login_required
def loan_eligibility_check(request):
    """View for checking loan eligibility."""
    if request.method == 'POST':
        form = LoanEligibilityForm(request.POST)
        if form.is_valid():
            # Get form data
            loan_type = form.cleaned_data['loan_type']
            requested_amount = form.cleaned_data['requested_amount']
            requested_term_months = form.cleaned_data['requested_term_months']
            monthly_income = form.cleaned_data['monthly_income']
            existing_monthly_debt = form.cleaned_data['existing_monthly_debt']
            credit_score = form.cleaned_data['credit_score']
            employment_years = form.cleaned_data['employment_years']
            
            # Calculate interest rate based on credit score
            interest_rate = calculate_interest_rate(loan_type, credit_score, employment_years)
            
            # Calculate monthly payment
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = (monthly_rate * requested_amount) / (1 - (1 + monthly_rate) ** -requested_term_months)
            
            # Calculate debt-to-income ratio
            dti_ratio = ((monthly_payment + existing_monthly_debt) / monthly_income) * 100
            
            # Determine eligibility
            is_eligible = (
                dti_ratio <= 43 and  # Standard DTI threshold
                credit_score >= 620 and  # Minimum credit score
                employment_years >= 1  # Minimum employment history
            )
            
            # Calculate maximum eligible amount
            max_eligible_amount = calculate_max_eligible_amount(
                monthly_income, existing_monthly_debt, interest_rate, requested_term_months
            ) if not is_eligible else requested_amount
            
            # Create eligibility record
            eligibility = LoanEligibility.objects.create(
                user=request.user,
                loan_type=loan_type,
                requested_amount=requested_amount,
                requested_term_months=requested_term_months,
                is_eligible=is_eligible,
                max_eligible_amount=max_eligible_amount,
                offered_interest_rate=interest_rate,
                reason=generate_eligibility_reason(is_eligible, dti_ratio, credit_score, employment_years)
            )
            
            return redirect('loan_eligibility_result', pk=eligibility.pk)
    else:
        form = LoanEligibilityForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'loans/loan_eligibility_check.html', context)

@login_required
def loan_eligibility_result(request, pk):
    """View for displaying loan eligibility results."""
    eligibility = get_object_or_404(LoanEligibility, pk=pk, user=request.user)
    
    # If eligible, calculate monthly payment
    monthly_payment = None
    if eligibility.is_eligible:
        monthly_rate = eligibility.offered_interest_rate / 100 / 12
        monthly_payment = (monthly_rate * eligibility.requested_amount) / (1 - (1 + monthly_rate) ** -eligibility.requested_term_months)
    
    context = {
        'eligibility': eligibility,
        'monthly_payment': monthly_payment,
    }
    
    return render(request, 'loans/loan_eligibility_result.html', context)

# Helper functions

def generate_payment_schedule(loan):
    """Generate payment schedule for a loan."""
    principal = loan.amount
    rate = loan.interest_rate / 100 / 12  # Monthly interest rate
    term = loan.term_months
    
    # Calculate monthly payment using the formula: P = (r * PV) / (1 - (1 + r)^-n)
    monthly_payment = (rate * principal) / (1 - (1 + rate) ** -term)
    
    # Update loan's monthly payment
    loan.monthly_payment = monthly_payment
    loan.save()
    
    # Generate payment schedule
    balance = principal
    payment_date = loan.start_date
    
    for month in range(1, term + 1):
        interest_payment = balance * rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        
        # Create payment record
        LoanPayment.objects.create(
            loan=loan,
            payment_date=payment_date,
            amount=monthly_payment,
            principal_amount=principal_payment,
            interest_amount=interest_payment,
            remaining_balance=max(0, balance),
            is_paid=payment_date < timezone.now().date()  # Mark past payments as paid
        )
        
        # Move to next month
        payment_date = payment_date + relativedelta(months=1)

def calculate_interest_rate(loan_type, credit_score, employment_years):
    """Calculate interest rate based on loan type, credit score, and employment history."""
    # Base rate from loan type
    base_rate = loan_type.base_interest_rate
    
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

def calculate_max_eligible_amount(monthly_income, existing_debt, interest_rate, term_months):
    """Calculate maximum eligible loan amount based on income and existing debt."""
    # Maximum DTI ratio (43%)
    max_dti = 0.43
    
    # Maximum monthly payment available
    max_payment = (monthly_income * max_dti) - existing_debt
    
    # If max payment is negative or zero, return 0
    if max_payment <= 0:
        return 0
    
    # Calculate maximum loan amount using the formula: PV = P * ((1 - (1 + r)^-n) / r)
    monthly_rate = interest_rate / 100 / 12
    max_amount = max_payment * ((1 - (1 + monthly_rate) ** -term_months) / monthly_rate)
    
    return max_amount

def generate_eligibility_reason(is_eligible, dti_ratio, credit_score, employment_years):
    """Generate a reason for loan eligibility decision."""
    reasons = []
    
    if dti_ratio > 43:
        reasons.append(f"Your debt-to-income ratio ({dti_ratio:.1f}%) exceeds our maximum threshold of 43%.")
    
    if credit_score < 620:
        reasons.append(f"Your credit score ({credit_score}) is below our minimum requirement of 620.")
    
    if employment_years < 1:
        reasons.append(f"Your employment history ({employment_years:.1f} years) is below our minimum requirement of 1 year.")
    
    if is_eligible:
        return "Congratulations! You are eligible for this loan."
    else:
        return "We are unable to approve your loan request for the following reasons: " + " ".join(reasons)
