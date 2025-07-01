from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import CreditEstimation, CreditFactor, CreditHistory, ImprovementSuggestion
from .forms import CreditHistoryForm, CreditEstimationForm, QuickCreditEstimationForm
import json
import numpy as np

@login_required
def credit_home(request):
    """View for the credit score dashboard."""
    # Get user's credit history
    credit_history = CreditHistory.objects.filter(
        user=request.user
    ).order_by('-date')
    
    # Get latest credit score
    latest_score = credit_history.first()
    
    # Get improvement suggestions
    suggestions = ImprovementSuggestion.objects.filter(
        credit_estimation__user=request.user,
        is_implemented=False
    ).order_by('-potential_points_gain')
    
    # Get credit factors (basic factors, not user-specific)
    factors = CreditFactor.objects.all().order_by('-weight')
    
    # Calculate score trend
    score_trend = []
    for history in credit_history:
        score_trend.append({
            'date': history.date.strftime('%Y-%m-%d'),
            'score': history.score,
            'source': history.report_source
        })
    
    context = {
        'credit_history': credit_history[:5],
        'latest_score': latest_score,
        'suggestions': suggestions,
        'factors': factors,
        'score_trend': json.dumps(score_trend),
    }
    
    return render(request, 'credit/credit_home.html', context)

@login_required
def credit_history_list(request):
    """View for listing credit history."""
    credit_history = CreditHistory.objects.filter(
        user=request.user
    ).order_by('-date')
    
    context = {
        'credit_history': credit_history,
    }
    
    return render(request, 'credit/credit_history_list.html', context)

@login_required
def credit_history_add(request):
    """View for adding a credit history entry."""
    if request.method == 'POST':
        form = CreditHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.user = request.user
            history.save()
            
            # Generate credit factors and suggestions based on new score
            generate_credit_factors(request.user, history.score)
            generate_improvement_suggestions(request.user, history.score)
            
            messages.success(request, 'Credit history entry added successfully!')
            return redirect('credit_home')
    else:
        form = CreditHistoryForm(initial={'date': timezone.now().date()})
    
    context = {
        'form': form,
        'title': 'Add Credit History',
    }
    
    return render(request, 'credit/credit_history_form.html', context)

@login_required
def credit_history_edit(request, pk):
    """View for editing a credit history entry."""
    history = get_object_or_404(CreditHistory, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CreditHistoryForm(request.POST, instance=history)
        if form.is_valid():
            form.save()
            messages.success(request, 'Credit history entry updated successfully!')
            return redirect('credit_history_list')
    else:
        form = CreditHistoryForm(instance=history)
    
    context = {
        'form': form,
        'history': history,
        'title': 'Edit Credit History',
    }
    
    return render(request, 'credit/credit_history_form.html', context)

@login_required
def credit_history_delete(request, pk):
    """View for deleting a credit history entry."""
    history = get_object_or_404(CreditHistory, pk=pk, user=request.user)
    
    if request.method == 'POST':
        history.delete()
        messages.success(request, 'Credit history entry deleted successfully!')
        return redirect('credit_history_list')
    
    context = {
        'history': history,
    }
    
    return render(request, 'credit/credit_history_confirm_delete.html', context)

@login_required
def credit_estimator(request):
    """View for estimating credit score."""
    if request.method == 'POST':
        form = CreditEstimationForm(request.POST)
        if form.is_valid():
            estimation = form.save(commit=False)
            estimation.user = request.user
            
            # Calculate credit score
            score = calculate_credit_score(estimation)
            estimation.estimated_score = score
            estimation.save()
            
            # Generate credit factors and suggestions
            generate_credit_factors(request.user, score, estimation)
            generate_improvement_suggestions(request.user, score, estimation)
            
            return redirect('credit_estimation_result', pk=estimation.pk)
    else:
        form = CreditEstimationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'credit/credit_estimator.html', context)

@login_required
def quick_credit_estimator(request):
    """View for quick credit score estimation."""
    if request.method == 'POST':
        form = QuickCreditEstimationForm(request.POST)
        if form.is_valid():
            # Get form data
            age = form.cleaned_data['age']
            ever_missed_payment = form.cleaned_data.get('ever_missed_payment', False)
            missed_payments_last_year = form.cleaned_data.get('missed_payments_last_year', 0)
            has_credit_cards = form.cleaned_data.get('has_credit_cards', False)
            credit_utilization = form.cleaned_data.get('credit_utilization', 'medium')
            oldest_account = form.cleaned_data['oldest_account']
            has_loans = form.cleaned_data.get('has_loans', False)
            has_mortgage = form.cleaned_data.get('has_mortgage', False)
            new_credit_last_year = form.cleaned_data.get('new_credit_last_year', False)
            
            # Calculate quick score
            score = calculate_quick_credit_score(
                age, ever_missed_payment, missed_payments_last_year,
                has_credit_cards, credit_utilization, oldest_account,
                has_loans, has_mortgage, new_credit_last_year
            )
            
            # Create estimation record
            estimation = CreditEstimation.objects.create(
                user=request.user,
                estimated_score=score,
                # Set some basic fields from the quick form
                missed_payments_count=1 if ever_missed_payment else 0,
                has_credit_cards=has_credit_cards,
                has_mortgage=has_mortgage,
                new_accounts_last_year=1 if new_credit_last_year else 0
            )
            
            # Generate credit factors and suggestions
            generate_credit_factors(request.user, score, estimation)
            generate_improvement_suggestions(request.user, score, estimation)
            
            return redirect('credit_estimation_result', pk=estimation.pk)
    else:
        form = QuickCreditEstimationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'credit/quick_credit_estimator.html', context)

@login_required
def credit_estimation_result(request, pk):
    """View for displaying credit estimation results."""
    estimation = get_object_or_404(CreditEstimation, pk=pk, user=request.user)
    
    # Get credit factors
    factors = CreditFactor.objects.filter(
        user=request.user,
        estimation=estimation
    ).order_by('-weight')
    
    # Get improvement suggestions
    suggestions = ImprovementSuggestion.objects.filter(
        user=request.user,
        estimation=estimation
    ).order_by('-impact_score')
    
    # Determine score category
    score = estimation.estimated_score
    if score >= 800:
        category = 'Excellent'
        category_description = 'You have an exceptional credit score that qualifies you for the best rates and terms.'
    elif score >= 740:
        category = 'Very Good'
        category_description = 'You have a very good credit score that qualifies you for better-than-average rates and terms.'
    elif score >= 670:
        category = 'Good'
        category_description = 'You have a good credit score that qualifies you for most loans at competitive rates.'
    elif score >= 580:
        category = 'Fair'
        category_description = 'You have a fair credit score that may qualify you for most loans but at higher interest rates.'
    else:
        category = 'Poor'
        category_description = 'You have a poor credit score that may make it difficult to qualify for loans or credit cards.'
    
    context = {
        'estimation': estimation,
        'factors': factors,
        'suggestions': suggestions,
        'score': score,
        'category': category,
        'category_description': category_description,
    }
    
    return render(request, 'credit/credit_estimation_result.html', context)

@login_required
def mark_suggestion_implemented(request, pk):
    """View for marking an improvement suggestion as implemented."""
    suggestion = get_object_or_404(ImprovementSuggestion, pk=pk, user=request.user)
    
    if request.method == 'POST':
        suggestion.is_implemented = True
        suggestion.implemented_date = timezone.now().date()
        suggestion.save()
        
        messages.success(request, 'Suggestion marked as implemented successfully!')
        return redirect('credit_home')
    
    context = {
        'suggestion': suggestion,
    }
    
    return render(request, 'credit/suggestion_confirm_implement.html', context)

@login_required
def credit_score_chart(request):
    """API view for credit score chart data."""
    # Get user's credit history
    credit_history = CreditHistory.objects.filter(
        user=request.user
    ).order_by('date')
    
    # Prepare chart data
    chart_data = []
    for history in credit_history:
        chart_data.append({
            'date': history.date.strftime('%Y-%m-%d'),
            'score': history.score,
            'source': history.report_source
        })
    
    return JsonResponse({'chart_data': chart_data})

@login_required
def credit_score_comparison(request):
    """View for comparing user's credit score with averages."""
    # Get user's latest credit score
    latest_score = CreditHistory.objects.filter(
        user=request.user
    ).order_by('-date').first()
    
    if not latest_score:
        # If no history, use latest estimation
        latest_estimation = CreditEstimation.objects.filter(
            user=request.user
        ).order_by('-created_at').first()
        
        if latest_estimation:
            user_score = latest_estimation.estimated_score
        else:
            messages.info(request, 'You need to add credit history or run an estimation first.')
            return redirect('credit_home')
    else:
        user_score = latest_score.score
    
    # National averages by age group (fictional data for demo)
    national_averages = {
        '18-29': 660,
        '30-39': 677,
        '40-49': 690,
        '50-59': 713,
        '60+': 731,
        'overall': 698
    }
    
    # Get user's age group
    user_profile = request.user.profile if hasattr(request.user, 'profile') else None
    if user_profile and user_profile.birth_date:
        today = timezone.now().date()
        age = today.year - user_profile.birth_date.year - ((today.month, today.day) < (user_profile.birth_date.month, user_profile.birth_date.day))
        
        if age < 30:
            age_group = '18-29'
        elif age < 40:
            age_group = '30-39'
        elif age < 50:
            age_group = '40-49'
        elif age < 60:
            age_group = '50-59'
        else:
            age_group = '60+'
    else:
        age_group = 'overall'
    
    # Compare with average
    average_score = national_averages[age_group]
    difference = user_score - average_score
    
    context = {
        'user_score': user_score,
        'average_score': average_score,
        'difference': difference,
        'age_group': age_group,
        'national_averages': national_averages,
    }
    
    return render(request, 'credit/credit_score_comparison.html', context)

# Helper functions

def calculate_credit_score(estimation):
    """Calculate credit score based on estimation data."""
    # Payment History (35%)
    payment_history_score = calculate_payment_history_score(
        estimation.missed_payments_count,
        estimation.late_payments_count,
        estimation.on_time_payments_streak
    )
    
    # Credit Utilization (30%)
    utilization_score = calculate_utilization_score(
        estimation.total_credit_limit,
        estimation.current_credit_usage
    )
    
    # Length of Credit History (15%)
    history_score = calculate_history_score(
        estimation.oldest_account_years,
        estimation.average_account_age_years
    )
    
    # Credit Mix (10%)
    mix_score = calculate_mix_score(
        estimation.has_credit_cards,
        estimation.has_installment_loans,
        estimation.has_mortgage,
        estimation.has_retail_accounts
    )
    
    # New Credit (10%)
    new_credit_score = calculate_new_credit_score(
        estimation.recent_inquiries_count,
        estimation.new_accounts_last_year
    )
    
    # Calculate weighted total (300-850 scale)
    total_score = (
        (payment_history_score * 0.35) +
        (utilization_score * 0.30) +
        (history_score * 0.15) +
        (mix_score * 0.10) +
        (new_credit_score * 0.10)
    ) * 550 + 300
    
    # Ensure score is within valid range
    return max(300, min(int(total_score), 850))

def calculate_payment_history_score(missed_payments, late_payments, on_time_streak):
    """Calculate payment history component score (0-1)."""
    # Missed payments have severe impact
    missed_payment_factor = max(0, 1 - (missed_payments * 0.15))
    
    # Late payments have moderate impact
    late_payment_factor = max(0, 1 - (late_payments * 0.05))
    
    # On-time streak has positive impact
    streak_factor = min(1, on_time_streak / 24)  # 24+ months of on-time payments is ideal
    
    # Combine factors with appropriate weights
    return (missed_payment_factor * 0.6) + (late_payment_factor * 0.3) + (streak_factor * 0.1)

def calculate_utilization_score(credit_limit, credit_usage):
    """Calculate credit utilization component score (0-1)."""
    if credit_limit <= 0:
        return 0.5  # Neutral score if no credit limit
    
    # Calculate utilization ratio
    utilization = credit_usage / credit_limit
    
    # Optimal utilization is under 30%
    if utilization <= 0.3:
        return 1.0 - (utilization / 0.3 * 0.1)  # Small penalty for any utilization
    elif utilization <= 0.5:
        return 0.9 - ((utilization - 0.3) / 0.2 * 0.2)  # Moderate penalty
    elif utilization <= 0.75:
        return 0.7 - ((utilization - 0.5) / 0.25 * 0.2)  # Larger penalty
    else:
        return max(0, 0.5 - ((utilization - 0.75) / 0.25 * 0.5))  # Severe penalty

def calculate_history_score(oldest_account_years, average_age_years):
    """Calculate length of credit history component score (0-1)."""
    # Oldest account factor (7+ years is ideal)
    oldest_factor = min(1, oldest_account_years / 7)
    
    # Average age factor (4+ years is ideal)
    average_factor = min(1, average_age_years / 4)
    
    # Combine factors with appropriate weights
    return (oldest_factor * 0.7) + (average_factor * 0.3)

def calculate_mix_score(has_credit_cards, has_installment_loans, has_mortgage, has_retail_accounts):
    """Calculate credit mix component score (0-1)."""
    # Count different types of credit
    count = sum([has_credit_cards, has_installment_loans, has_mortgage, has_retail_accounts])
    
    # Score based on diversity (3+ types is ideal)
    return min(1, count / 3)

def calculate_new_credit_score(recent_inquiries, new_accounts):
    """Calculate new credit component score (0-1)."""
    # Inquiries factor (0 is ideal, 6+ is poor)
    inquiries_factor = max(0, 1 - (recent_inquiries / 6))
    
    # New accounts factor (0 is ideal, 3+ is poor)
    new_accounts_factor = max(0, 1 - (new_accounts / 3))
    
    # Combine factors with appropriate weights
    return (inquiries_factor * 0.6) + (new_accounts_factor * 0.4)

def calculate_quick_credit_score(age, ever_missed_payment, missed_payments_last_year,
                                has_credit_cards, credit_utilization, oldest_account,
                                has_loans, has_mortgage, new_credit_last_year):
    """Calculate a quick credit score estimate based on simplified inputs."""
    # Base score
    score = 650
    
    # Payment History (35%)
    if ever_missed_payment:
        score -= 30
    if missed_payments_last_year > 0:
        score -= 20 * missed_payments_last_year
    
    # Credit Utilization (30%)
    if has_credit_cards:
        if credit_utilization == 'low':
            score += 40
        elif credit_utilization == 'medium':
            score += 10
        elif credit_utilization == 'high':
            score -= 40
    
    # Length of Credit History (15%)
    if oldest_account == 'less_than_1':
        score -= 30
    elif oldest_account == '1_to_3':
        score -= 10
    elif oldest_account == '3_to_5':
        score += 10
    elif oldest_account == '5_to_10':
        score += 30
    elif oldest_account == 'more_than_10':
        score += 50
    
    # Credit Mix (10%)
    mix_count = sum([has_credit_cards, has_loans, has_mortgage])
    score += 10 * mix_count
    
    # New Credit (10%)
    if new_credit_last_year:
        score -= 10
    
    # Age factor (older consumers tend to have higher scores)
    if age >= 60:
        score += 20
    elif age >= 45:
        score += 10
    elif age <= 25:
        score -= 10
    
    # Ensure score is within valid range
    return max(300, min(score, 850))

def generate_credit_factors(user, score, estimation=None):
    """Generate credit factors based on score and estimation data."""
    # Clear existing factors for this estimation
    if estimation:
        CreditFactor.objects.filter(user=user, estimation=estimation).delete()
    
    factors = []
    
    if estimation:
        # Payment History
        payment_history_weight = 35
        if estimation.missed_payments_count > 0:
            factors.append({
                'name': 'Missed Payments',
                'description': f'You have {estimation.missed_payments_count} missed payments on your credit report.',
                'impact': 'negative',
                'weight': payment_history_weight
            })
        elif estimation.late_payments_count > 0:
            factors.append({
                'name': 'Late Payments',
                'description': f'You have {estimation.late_payments_count} late payments on your credit report.',
                'impact': 'negative',
                'weight': payment_history_weight
            })
        else:
            factors.append({
                'name': 'Payment History',
                'description': 'You have a strong history of on-time payments.',
                'impact': 'positive',
                'weight': payment_history_weight
            })
        
        # Credit Utilization
        utilization_weight = 30
        if estimation.total_credit_limit > 0:
            utilization = estimation.current_credit_usage / estimation.total_credit_limit * 100
            if utilization <= 10:
                factors.append({
                    'name': 'Credit Utilization',
                    'description': f'Your credit utilization is very low at {utilization:.1f}%.',
                    'impact': 'positive',
                    'weight': utilization_weight
                })
            elif utilization <= 30:
                factors.append({
                    'name': 'Credit Utilization',
                    'description': f'Your credit utilization is good at {utilization:.1f}%.',
                    'impact': 'positive',
                    'weight': utilization_weight
                })
            elif utilization <= 50:
                factors.append({
                    'name': 'Credit Utilization',
                    'description': f'Your credit utilization is moderate at {utilization:.1f}%.',
                    'impact': 'neutral',
                    'weight': utilization_weight
                })
            else:
                factors.append({
                    'name': 'Credit Utilization',
                    'description': f'Your credit utilization is high at {utilization:.1f}%.',
                    'impact': 'negative',
                    'weight': utilization_weight
                })
        
        # Length of Credit History
        history_weight = 15
        if estimation.oldest_account_years >= 7:
            factors.append({
                'name': 'Credit History Length',
                'description': f'You have a long credit history of {estimation.oldest_account_years} years.',
                'impact': 'positive',
                'weight': history_weight
            })
        elif estimation.oldest_account_years >= 3:
            factors.append({
                'name': 'Credit History Length',
                'description': f'You have a moderate credit history of {estimation.oldest_account_years} years.',
                'impact': 'neutral',
                'weight': history_weight
            })
        else:
            factors.append({
                'name': 'Credit History Length',
                'description': f'You have a short credit history of {estimation.oldest_account_years} years.',
                'impact': 'negative',
                'weight': history_weight
            })
        
        # Credit Mix
        mix_weight = 10
        credit_types = sum([
            estimation.has_credit_cards,
            estimation.has_installment_loans,
            estimation.has_mortgage,
            estimation.has_retail_accounts
        ])
        if credit_types >= 3:
            factors.append({
                'name': 'Credit Mix',
                'description': 'You have a diverse mix of credit types.',
                'impact': 'positive',
                'weight': mix_weight
            })
        elif credit_types >= 2:
            factors.append({
                'name': 'Credit Mix',
                'description': 'You have a moderate mix of credit types.',
                'impact': 'neutral',
                'weight': mix_weight
            })
        else:
            factors.append({
                'name': 'Credit Mix',
                'description': 'You have a limited mix of credit types.',
                'impact': 'negative',
                'weight': mix_weight
            })
        
        # New Credit
        new_credit_weight = 10
        if estimation.recent_inquiries_count > 3 or estimation.new_accounts_last_year > 2:
            factors.append({
                'name': 'New Credit',
                'description': f'You have {estimation.recent_inquiries_count} recent inquiries and {estimation.new_accounts_last_year} new accounts.',
                'impact': 'negative',
                'weight': new_credit_weight
            })
        elif estimation.recent_inquiries_count > 0 or estimation.new_accounts_last_year > 0:
            factors.append({
                'name': 'New Credit',
                'description': f'You have {estimation.recent_inquiries_count} recent inquiries and {estimation.new_accounts_last_year} new accounts.',
                'impact': 'neutral',
                'weight': new_credit_weight
            })
        else:
            factors.append({
                'name': 'New Credit',
                'description': 'You have no recent credit inquiries or new accounts.',
                'impact': 'positive',
                'weight': new_credit_weight
            })
    else:
        # Generic factors based on score
        if score >= 750:
            factors = [
                {
                    'name': 'Payment History',
                    'description': 'You have an excellent history of on-time payments.',
                    'impact': 'positive',
                    'weight': 35
                },
                {
                    'name': 'Credit Utilization',
                    'description': 'You maintain low credit card balances relative to your credit limits.',
                    'impact': 'positive',
                    'weight': 30
                },
                {
                    'name': 'Credit History Length',
                    'description': 'You have a well-established credit history.',
                    'impact': 'positive',
                    'weight': 15
                },
                {
                    'name': 'Credit Mix',
                    'description': 'You have a diverse mix of credit accounts.',
                    'impact': 'positive',
                    'weight': 10
                },
                {
                    'name': 'New Credit',
                    'description': 'You have few recent credit inquiries.',
                    'impact': 'positive',
                    'weight': 10
                }
            ]
        elif score >= 670:
            factors = [
                {
                    'name': 'Payment History',
                    'description': 'You have a good history of on-time payments with few or no late payments.',
                    'impact': 'positive',
                    'weight': 35
                },
                {
                    'name': 'Credit Utilization',
                    'description': 'Your credit utilization is generally good but could be improved.',
                    'impact': 'neutral',
                    'weight': 30
                },
                {
                    'name': 'Credit History Length',
                    'description': 'You have an established credit history.',
                    'impact': 'positive',
                    'weight': 15
                },
                {
                    'name': 'Credit Mix',
                    'description': 'You have a reasonable mix of credit types.',
                    'impact': 'neutral',
                    'weight': 10
                },
                {
                    'name': 'New Credit',
                    'description': 'You have a moderate number of recent credit inquiries.',
                    'impact': 'neutral',
                    'weight': 10
                }
            ]
        else:
            factors = [
                {
                    'name': 'Payment History',
                    'description': 'You may have some late or missed payments affecting your score.',
                    'impact': 'negative',
                    'weight': 35
                },
                {
                    'name': 'Credit Utilization',
                    'description': 'Your credit card balances may be too high relative to your credit limits.',
                    'impact': 'negative',
                    'weight': 30
                },
                {
                    'name': 'Credit History Length',
                    'description': 'Your credit history may be limited or relatively new.',
                    'impact': 'negative',
                    'weight': 15
                },
                {
                    'name': 'Credit Mix',
                    'description': 'You may have a limited variety of credit types.',
                    'impact': 'negative',
                    'weight': 10
                },
                {
                    'name': 'New Credit',
                    'description': 'You may have too many recent credit applications.',
                    'impact': 'negative',
                    'weight': 10
                }
            ]
    
    # Save factors to database
    for factor in factors:
        CreditFactor.objects.create(
            user=user,
            estimation=estimation,
            name=factor['name'],
            description=factor['description'],
            impact=factor['impact'],
            weight=factor['weight']
        )

def generate_improvement_suggestions(user, score, estimation=None):
    """Generate improvement suggestions based on score and estimation data."""
    # Clear existing suggestions for this estimation
    if estimation:
        ImprovementSuggestion.objects.filter(user=user, estimation=estimation).delete()
    
    suggestions = []
    
    if estimation:
        # Payment History suggestions
        if estimation.missed_payments_count > 0 or estimation.late_payments_count > 0:
            suggestions.append({
                'title': 'Set up automatic payments',
                'description': 'Set up automatic payments for at least the minimum payment amount to avoid missed or late payments in the future.',
                'impact_score': 9,
                'timeframe': 'immediate',
                'difficulty': 'easy'
            })
        
        # Credit Utilization suggestions
        if estimation.total_credit_limit > 0:
            utilization = estimation.current_credit_usage / estimation.total_credit_limit * 100
            if utilization > 30:
                suggestions.append({
                    'title': 'Reduce credit card balances',
                    'description': f'Work on paying down your credit card balances to get your utilization below 30%. Currently at {utilization:.1f}%.',
                    'impact_score': 8,
                    'timeframe': 'medium',
                    'difficulty': 'medium'
                })
                
                suggestions.append({
                    'title': 'Request credit limit increases',
                    'description': 'If you have a good payment history with your current cards, request credit limit increases to improve your utilization ratio.',
                    'impact_score': 7,
                    'timeframe': 'short',
                    'difficulty': 'easy'
                })
        
        # Credit Mix suggestions
        credit_types = sum([
            estimation.has_credit_cards,
            estimation.has_installment_loans,
            estimation.has_mortgage,
            estimation.has_retail_accounts
        ])
        
        if credit_types < 2:
            suggestions.append({
                'title': 'Diversify your credit mix',
                'description': 'Consider adding a different type of credit to your profile, such as a small installment loan or a secured credit card.',
                'impact_score': 6,
                'timeframe': 'medium',
                'difficulty': 'medium'
            })
        
        # New Credit suggestions
        if estimation.recent_inquiries_count > 3:
            suggestions.append({
                'title': 'Limit new credit applications',
                'description': 'Avoid applying for new credit for the next 6-12 months to allow recent inquiries to age.',
                'impact_score': 5,
                'timeframe': 'long',
                'difficulty': 'medium'
            })
        
        # Length of Credit History suggestions
        if estimation.oldest_account_years < 2:
            suggestions.append({
                'title': 'Keep oldest accounts open',
                'description': 'Maintain your oldest credit accounts to preserve the length of your credit history.',
                'impact_score': 7,
                'timeframe': 'ongoing',
                'difficulty': 'easy'
            })
    else:
        # Generic suggestions based on score
        if score < 670:
            suggestions = [
                {
                    'title': 'Pay all bills on time',
                    'description': 'Set up automatic payments or reminders to ensure all bills are paid on time.',
                    'impact_score': 9,
                    'timeframe': 'immediate',
                    'difficulty': 'easy'
                },
                {
                    'title': 'Reduce credit card balances',
                    'description': 'Work on paying down your credit card balances to below 30% of your credit limits.',
                    'impact_score': 8,
                    'timeframe': 'medium',
                    'difficulty': 'medium'
                },
                {
                    'title': 'Dispute any errors on your credit report',
                    'description': 'Check your credit reports for errors and dispute any inaccuracies.',
                    'impact_score': 7,
                    'timeframe': 'short',
                    'difficulty': 'medium'
                }
            ]
        elif score < 740:
            suggestions = [
                {
                    'title': 'Keep credit card utilization low',
                    'description': 'Aim to keep your credit card balances below 10% of your credit limits for optimal scores.',
                    'impact_score': 7,
                    'timeframe': 'short',
                    'difficulty': 'medium'
                },
                {
                    'title': 'Avoid closing old credit accounts',
                    'description': 'Keep your oldest accounts open to maintain a long credit history.',
                    'impact_score': 6,
                    'timeframe': 'ongoing',
                    'difficulty': 'easy'
                },
                {
                    'title': 'Limit applications for new credit',
                    'description': 'Only apply for new credit when necessary to minimize hard inquiries.',
                    'impact_score': 5,
                    'timeframe': 'ongoing',
                    'difficulty': 'easy'
                }
            ]
        else:
            suggestions = [
                {
                    'title': 'Maintain your excellent habits',
                    'description': 'Continue your good credit practices to maintain your excellent score.',
                    'impact_score': 5,
                    'timeframe': 'ongoing',
                    'difficulty': 'easy'
                },
                {
                    'title': 'Monitor your credit regularly',
                    'description': 'Check your credit reports regularly to ensure accuracy and detect fraud early.',
                    'impact_score': 4,
                    'timeframe': 'ongoing',
                    'difficulty': 'easy'
                }
            ]
    
    # Save suggestions to database
    for suggestion in suggestions:
        ImprovementSuggestion.objects.create(
            user=user,
            estimation=estimation,
            title=suggestion['title'],
            description=suggestion['description'],
            impact_score=suggestion['impact_score'],
            timeframe=suggestion['timeframe'],
            difficulty=suggestion['difficulty']
        )
