#!/usr/bin/env python
"""
Standalone script to create sample data for FinWise AI
Run with: python create_sample_data.py
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Import all models
from accounts.models import User, UserProfile
from expenses.models import ExpenseCategory, Expense
from goals.models import SavingsGoal, GoalContribution
from loans.models import LoanType, Loan
from investments.models import InvestmentType, Investment
from credit.models import CreditHistory, CreditFactor, CreditFactorScore

def create_sample_data():
    print("🚀 Creating sample data for FinWise AI...")
    
    # Create test user with proper password
    print("👤 Creating test user...")
    try:
        user = User.objects.get(email='testuser@finwise.ai')
        print(f"   User already exists: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='testuser@finwise.ai',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            is_verified=True
        )
        print(f"   ✅ Created user: {user.email}")
    
    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'phone_number': '+1234567890',
            'date_of_birth': datetime(1990, 5, 15).date(),
            'monthly_income': Decimal('5500.00'),
            'occupation': 'Software Engineer',
            'financial_goals': 'Save for house down payment and retirement'
        }
    )
    if created:
        print("   ✅ Created user profile")
    else:
        print("   User profile already exists")

    # Create expense categories
    print("💰 Creating expense categories...")
    categories_data = [
        ('Food & Dining', '#FF6B6B', 'Restaurant meals, groceries, and food delivery'),
        ('Transportation', '#4ECDC4', 'Gas, public transit, ride-sharing, car maintenance'),
        ('Housing', '#45B7D1', 'Rent, mortgage, utilities, home maintenance'),
        ('Entertainment', '#96CEB4', 'Movies, concerts, streaming services, hobbies'),
        ('Shopping', '#FFEAA7', 'Clothing, electronics, personal items'),
        ('Healthcare', '#DDA0DD', 'Medical bills, prescriptions, insurance'),
        ('Personal Care', '#85C1E9', 'Haircuts, cosmetics, gym membership'),
    ]
    
    categories = []
    for name, color, desc in categories_data:
        category, created = ExpenseCategory.objects.get_or_create(
            name=name,
            defaults={'color': color, 'description': desc}
        )
        categories.append(category)
        if created:
            print(f"   ✅ Created expense category: {name}")

    # Create sample expenses
    print("📊 Creating sample expenses...")
    start_date = timezone.now().date() - timedelta(days=90)
    
    sample_expenses = [
        ('Grocery Shopping', categories[0], 85.50, 6),  # 6 times
        ('Restaurant Dinner', categories[0], 45.00, 4),
        ('Gas Station', categories[1], 55.00, 8),
        ('Rent Payment', categories[2], 1200.00, 3),
        ('Netflix Subscription', categories[3], 15.99, 3),
        ('Gym Membership', categories[6], 45.00, 3),
        ('Coffee Shop', categories[0], 12.50, 10),
        ('Uber Ride', categories[1], 18.50, 5),
        ('Movie Theater', categories[3], 24.00, 2),
        ('Doctor Visit', categories[5], 150.00, 1),
    ]
    
    expense_count = 0
    for desc, category, amount, count in sample_expenses:
        for i in range(count):
            expense_date = start_date + timedelta(days=random.randint(0, 90))
            expense, created = Expense.objects.get_or_create(
                user=user,
                description=f"{desc} #{i+1}",
                date=expense_date,
                defaults={
                    'amount': Decimal(str(amount + random.uniform(-10, 10))),
                    'category': category,
                    'notes': f'Sample expense entry',
                    'is_flagged': False
                }
            )
            if created:
                expense_count += 1
    
    print(f"   ✅ Created {expense_count} sample expenses")

    # Create savings goals
    print("🎯 Creating savings goals...")
    goals_data = [
        ('Emergency Fund', 10000.00, 'Build 6-month emergency fund', 'high', 'emergency'),
        ('House Down Payment', 50000.00, 'Save for first home down payment', 'high', 'home'),
        ('Vacation Fund', 5000.00, 'European vacation next summer', 'medium', 'travel'),
        ('New Car', 25000.00, 'Replace old car with reliable vehicle', 'medium', 'transportation'),
    ]
    
    goal_count = 0
    for name, target, desc, priority, category in goals_data:
        target_date = timezone.now().date() + timedelta(days=random.randint(365, 1095))
        
        goal, created = SavingsGoal.objects.get_or_create(
            user=user,
            name=name,
            defaults={
                'description': desc,
                'target_amount': Decimal(str(target)),
                'current_amount': Decimal('0.00'),
                'target_date': target_date,
                'priority': priority,
                'category': category,
                'status': 'active'
            }
        )
        
        if created:
            goal_count += 1
            # Add some contributions
            contribution_amount = target / 15
            for i in range(random.randint(1, 4)):
                contrib_date = timezone.now().date() - timedelta(days=random.randint(0, 90))
                contrib_amount = Decimal(str(contribution_amount + random.uniform(-50, 100)))
                
                GoalContribution.objects.create(
                    goal=goal,
                    amount=contrib_amount,
                    date=contrib_date,
                    description=f'Monthly contribution #{i+1}'
                )
                
                goal.current_amount += contrib_amount
            
            goal.save()
    
    print(f"   ✅ Created {goal_count} savings goals")

    # Create loan types
    print("🏦 Creating loan types...")
    loan_types_data = [
        ('Personal Loan', 'Unsecured personal loans for various purposes'),
        ('Auto Loan', 'Vehicle financing loans'),
        ('Student Loan', 'Education financing loans'),
        ('Credit Card', 'Revolving credit accounts'),
    ]
    
    loan_types = []
    lt_count = 0
    for name, desc in loan_types_data:
        loan_type, created = LoanType.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        loan_types.append(loan_type)
        if created:
            lt_count += 1
    
    print(f"   ✅ Created {lt_count} loan types")

    # Create sample loans
    print("💳 Creating sample loans...")
    loans_data = [
        ('Car Loan', loan_types[1], 18500.00, 4.5, 60, 'active'),
        ('Personal Loan', loan_types[0], 5000.00, 8.2, 36, 'active'),
        ('Student Loan', loan_types[2], 12000.00, 6.8, 120, 'active'),
    ]
    
    loan_count = 0
    for name, loan_type, amount, rate, term, status in loans_data:
        monthly_rate = rate / 100 / 12
        monthly_payment = amount * (monthly_rate * (1 + monthly_rate)**term) / ((1 + monthly_rate)**term - 1)
        start_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
        
        loan, created = Loan.objects.get_or_create(
            user=user,
            name=name,
            defaults={
                'loan_type': loan_type,
                'amount': Decimal(str(amount)),
                'interest_rate': Decimal(str(rate)),
                'term_months': term,
                'monthly_payment': Decimal(str(monthly_payment)),
                'start_date': start_date,
                'status': status,
                'description': f'{name} - {loan_type.name}'
            }
        )
        
        if created:
            loan_count += 1
    
    print(f"   ✅ Created {loan_count} loans")

    # Create investment types
    print("📈 Creating investment types...")
    investment_types_data = [
        ('Stocks', 'Individual company stocks'),
        ('ETFs', 'Exchange-traded funds'),
        ('Mutual Funds', 'Actively managed mutual funds'),
        ('Cryptocurrency', 'Digital currencies and tokens'),
    ]
    
    investment_types = []
    it_count = 0
    for name, desc in investment_types_data:
        inv_type, created = InvestmentType.objects.get_or_create(
            name=name,
            defaults={'description': desc}
        )
        investment_types.append(inv_type)
        if created:
            it_count += 1
    
    print(f"   ✅ Created {it_count} investment types")

    # Create sample investments
    print("💎 Creating sample investments...")
    investments_data = [
        ('Apple Inc. (AAPL)', investment_types[0], 'AAPL', 2500.00, 175.50, 7.5),
        ('S&P 500 ETF (SPY)', investment_types[1], 'SPY', 5000.00, 425.00, 8.2),
        ('Vanguard Total Stock Market', investment_types[2], 'VTSAX', 3000.00, 95.25, 9.1),
        ('Bitcoin', investment_types[3], 'BTC', 1000.00, 45000.00, 15.8),
    ]
    
    inv_count = 0
    for name, inv_type, symbol, amount, price, expected_return in investments_data:
        purchase_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
        quantity = amount / price
        
        investment, created = Investment.objects.get_or_create(
            user=user,
            symbol=symbol,
            defaults={
                'investment_type': inv_type,
                'purchase_amount': Decimal(str(amount)),
                'purchase_price': Decimal(str(price)),
                'quantity': Decimal(str(quantity)),
                'purchase_date': purchase_date,
                'expected_return': Decimal(str(expected_return)),
                'is_active': True,
                'auto_track': True,
                'notes': f'Investment in {name}'
            }
        )
        
        if created:
            inv_count += 1
    
    print(f"   ✅ Created {inv_count} investments")

    # Create credit factors
    print("🏆 Creating credit factors...")
    factors_data = [
        ('Payment History', 'On-time payment record', 35.0),
        ('Credit Utilization', 'Percentage of available credit used', 30.0),
        ('Length of Credit History', 'Age of credit accounts', 15.0),
        ('Credit Mix', 'Variety of credit account types', 10.0),
        ('New Credit', 'Recent credit inquiries and accounts', 10.0),
    ]
    
    factors = []
    cf_count = 0
    for name, desc, weight in factors_data:
        factor, created = CreditFactor.objects.get_or_create(
            name=name,
            defaults={'description': desc, 'weight': Decimal(str(weight))}
        )
        factors.append(factor)
        if created:
            cf_count += 1
    
    print(f"   ✅ Created {cf_count} credit factors")

    # Create credit history
    print("📋 Creating credit history...")
    start_date = timezone.now().date() - timedelta(days=365)
    base_score = 725
    ch_count = 0
    
    for i in range(6):  # 6 months
        score_date = start_date + timedelta(days=60*i)
        score_variation = random.randint(-10, 10)
        current_score = max(300, min(850, base_score + score_variation))
        
        credit_history, created = CreditHistory.objects.get_or_create(
            user=user,
            date=score_date,
            defaults={
                'score': current_score,
                'report_source': random.choice(['Experian', 'Equifax', 'TransUnion']),
                'notes': 'Monthly credit score update'
            }
        )
        
        if created:
            ch_count += 1
            # Add factor scores
            for factor in factors:
                factor_score = random.randint(70, 95)
                CreditFactorScore.objects.create(
                    credit_history=credit_history,
                    factor=factor,
                    score=factor_score,
                    notes=f'Factor score for {factor.name}'
                )
        
        base_score = current_score
    
    print(f"   ✅ Created {ch_count} credit history entries")
    
    print("\n🎉 Sample data creation completed successfully!")
    print("\n📋 Summary of created data:")
    print(f"   • User: testuser@finwise.ai (password: testpass123)")
    print(f"   • Expense categories: {len(categories)}")
    print(f"   • Expenses: {expense_count}")
    print(f"   • Savings goals: {goal_count}")
    print(f"   • Loan types: {len(loan_types)}")
    print(f"   • Loans: {loan_count}")
    print(f"   • Investment types: {len(investment_types)}")
    print(f"   • Investments: {inv_count}")
    print(f"   • Credit factors: {len(factors)}")
    print(f"   • Credit history entries: {ch_count}")
    print("\n🚀 You can now login and test all features!")
    print("   Login URL: http://127.0.0.1:8000/accounts/login/")

if __name__ == '__main__':
    try:
        create_sample_data()
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc() 