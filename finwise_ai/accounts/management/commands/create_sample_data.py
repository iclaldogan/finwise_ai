from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

from accounts.models import UserProfile
from expenses.models import ExpenseCategory, Expense, RecurringExpense, AnomalyDetection
from loans.models import LoanType, Loan
from goals.models import SavingsGoal, GoalContribution
from investments.models import InvestmentType, Investment, InvestmentTransaction
from credit.models import CreditFactor, CreditEstimation, CreditHistory, CreditFactorScore, ImprovementSuggestion

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample data for testing and demonstration purposes'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create demo user if it doesn't exist
        if not User.objects.filter(email='demo@finwiseai.com').exists():
            demo_user = User.objects.create_user(
                email='demo@finwiseai.com',
                password='demopassword',
                first_name='Demo',
                last_name='User',
                is_active=True,
                email_verified=True
            )
            self.stdout.write(self.style.SUCCESS(f'Created demo user: {demo_user.email}'))
            
            # Create user profile
            UserProfile.objects.create(
                user=demo_user,
                monthly_income=Decimal('15000.00'),
                preferred_currency='TRY',
                risk_profile='moderate',
                date_of_birth=timezone.now().date() - timedelta(days=365*30),
                phone_number='+905551234567',
                savings_focused=True,
                investment_focused=True,
                budget_conscious=True
            )
            self.stdout.write(self.style.SUCCESS('Created user profile'))
        else:
            demo_user = User.objects.get(email='demo@finwiseai.com')
            self.stdout.write('Demo user already exists, using existing user')
        
        # Create expense categories if they don't exist
        categories = [
            'Rent', 'Groceries', 'Utilities', 'Transportation', 
            'Dining', 'Entertainment', 'Healthcare', 'Education', 'Subscriptions'
        ]
        
        category_objects = []
        for category_name in categories:
            category, created = ExpenseCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'color': f'#{random.randint(0, 0xFFFFFF):06x}',
                    'icon': 'fa-solid fa-circle'
                }
            )
            category_objects.append(category)
            if created:
                self.stdout.write(f'Created category: {category_name}')
        
        self.stdout.write(self.style.SUCCESS('Created expense categories'))
        
        # Create sample expenses
        if Expense.objects.filter(user=demo_user).count() < 20:
            # Create expenses for the last 3 months
            for month in range(3):
                for _ in range(20):
                    expense_date = timezone.now() - timedelta(days=month*30 + random.randint(0, 29))
                    Expense.objects.create(
                        user=demo_user,
                        category=random.choice(category_objects),
                        amount=Decimal(str(random.randint(10, 1000) + random.random())).quantize(Decimal('0.01')),
                        description=f"Sample expense {random.randint(1000, 9999)}",
                        date=expense_date
                    )
            self.stdout.write(self.style.SUCCESS('Created sample expenses'))
        
        # Create recurring expenses
        if RecurringExpense.objects.filter(parent_expense__user=demo_user).count() < 5:
            # First create parent expenses
            for category in random.sample(category_objects, 5):
                parent_expense = Expense.objects.create(
                    user=demo_user,
                    category=category,
                    amount=Decimal(str(random.randint(100, 2000) + random.random())).quantize(Decimal('0.01')),
                    description=f"Recurring {category.name.lower()}",
                    date=timezone.now() - timedelta(days=30),
                    recurrence='monthly'
                )
                
                # Create recurring instances
                for i in range(1, 4):  # Create 3 future instances
                    RecurringExpense.objects.create(
                        parent_expense=parent_expense,
                        amount=parent_expense.amount,
                        date=timezone.now() + timedelta(days=30*i),
                        is_paid=False
                    )
            self.stdout.write(self.style.SUCCESS('Created recurring expenses'))
        
        # Create some anomalies
        if AnomalyDetection.objects.filter(user=demo_user).count() < 3:
            expenses = Expense.objects.filter(user=demo_user).order_by('?')[:3]
            anomaly_types = ['spike', 'fraud_flag', 'unusual_pattern']
            
            for i, expense in enumerate(expenses):
                AnomalyDetection.objects.create(
                    user=demo_user,
                    expense=expense,
                    anomaly_type=anomaly_types[i % len(anomaly_types)],
                    confidence_score=random.uniform(0.7, 0.95),
                    description=f"Potential {anomaly_types[i % len(anomaly_types)]} detected",
                    is_reviewed=False
                )
            self.stdout.write(self.style.SUCCESS('Created anomaly detections'))
        
        # Create loan types if they don't exist
        loan_types = [
            {'name': 'Personal Loan', 'description': 'General purpose personal loan'},
            {'name': 'Mortgage', 'description': 'Home loan for property purchase'},
            {'name': 'Auto Loan', 'description': 'Loan for vehicle purchase'},
            {'name': 'Student Loan', 'description': 'Loan for educational expenses'}
        ]
        
        for loan_type in loan_types:
            LoanType.objects.get_or_create(
                name=loan_type['name'],
                defaults={'description': loan_type['description']}
            )
        self.stdout.write(self.style.SUCCESS('Created loan types'))
        
        # Create sample loans
        if Loan.objects.filter(user=demo_user).count() < 2:
            loan_types = LoanType.objects.all()
            
            # Create a mortgage
            mortgage_type = LoanType.objects.get(name='Mortgage')
            Loan.objects.create(
                user=demo_user,
                loan_type=mortgage_type,
                amount=Decimal('500000.00'),
                interest_rate=Decimal('0.89'),
                term_months=240,
                monthly_payment=Decimal('2934.12'),
                start_date=timezone.now() - timedelta(days=365),
                end_date=timezone.now() + timedelta(days=365*19),
                remaining_balance=Decimal('480000.00'),
                status='active'
            )
            
            # Create an auto loan
            auto_type = LoanType.objects.get(name='Auto Loan')
            Loan.objects.create(
                user=demo_user,
                loan_type=auto_type,
                amount=Decimal('120000.00'),
                interest_rate=Decimal('1.2'),
                term_months=48,
                monthly_payment=Decimal('2875.34'),
                start_date=timezone.now() - timedelta(days=180),
                end_date=timezone.now() + timedelta(days=365*3 + 180),
                remaining_balance=Decimal('100000.00'),
                status='active'
            )
            self.stdout.write(self.style.SUCCESS('Created sample loans'))
        
        # Create savings goals
        if SavingsGoal.objects.filter(user=demo_user).count() < 3:
            goals = [
                {'name': 'Emergency Fund', 'target_amount': Decimal('30000.00'), 'months': 6},
                {'name': 'Vacation', 'target_amount': Decimal('15000.00'), 'months': 3},
                {'name': 'New Laptop', 'target_amount': Decimal('20000.00'), 'months': 4}
            ]
            
            today = timezone.now().date()
            
            for goal in goals:
                # Set start_date to today and target_date to future
                start_date = today
                target_date = today + timedelta(days=30*goal['months'])
                
                savings_goal = SavingsGoal.objects.create(
                    user=demo_user,
                    name=goal['name'],
                    target_amount=goal['target_amount'],
                    current_amount=Decimal(str(random.randint(0, int(goal['target_amount']/2)))),
                    start_date=start_date,  # Add start_date
                    target_date=target_date,
                    description=f"Saving for {goal['name'].lower()}",
                    status='active',
                    priority='medium'
                )
                
                # Add some contributions
                for _ in range(random.randint(2, 5)):
                    contribution_date = today - timedelta(days=random.randint(1, 30))
                    # Ensure contribution date is not before start date
                    if contribution_date < start_date:
                        contribution_date = start_date
                        
                    GoalContribution.objects.create(
                        goal=savings_goal,
                        amount=Decimal(str(random.randint(500, 2000))),
                        date=contribution_date,
                        notes="Regular contribution"
                    )
            self.stdout.write(self.style.SUCCESS('Created savings goals and contributions'))
        
        # Create investment types if they don't exist
        investment_types = [
            {'name': 'Stocks', 'category': 'stocks', 'description': 'Individual company stocks', 'risk_level': 5},
            {'name': 'Bonds', 'category': 'bonds', 'description': 'Government and corporate bonds', 'risk_level': 1},
            {'name': 'Mutual Funds', 'category': 'mutual_funds', 'description': 'Diversified investment funds', 'risk_level': 3},
            {'name': 'Cryptocurrencies', 'category': 'crypto', 'description': 'Digital currencies', 'risk_level': 5}
        ]
        
        for inv_type in investment_types:
            InvestmentType.objects.get_or_create(
                name=inv_type['name'],
                defaults={
                    'category': inv_type['category'],
                    'description': inv_type['description'],
                    'risk_level': inv_type['risk_level']
                }
            )
        self.stdout.write(self.style.SUCCESS('Created investment types'))
        
        # Create sample investments
        if Investment.objects.filter(user=demo_user).count() < 4:
            investment_types = InvestmentType.objects.all()
            
            for inv_type in investment_types:
                purchase_date = timezone.now().date() - timedelta(days=random.randint(30, 365))
                purchase_price = Decimal(str(random.randint(50, 500) + random.random())).quantize(Decimal('0.01'))
                quantity = Decimal(str(random.randint(10, 100) + random.random())).quantize(Decimal('0.01'))
                
                investment = Investment.objects.create(
                    user=demo_user,
                    investment_type=inv_type,
                    name=f"{inv_type.name} Portfolio",
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    quantity=quantity,
                    current_price=purchase_price * Decimal(str(random.uniform(0.8, 1.2))).quantize(Decimal('0.01')),
                    last_updated=timezone.now(),
                    status='active',
                    is_simulation=False,
                    notes=f"Investment in {inv_type.name.lower()}"
                )
                
                # Add some transactions
                for _ in range(random.randint(3, 8)):
                    transaction_date = timezone.now().date() - timedelta(days=random.randint(1, 180))
                    transaction_type = random.choice(['buy', 'sell'])
                    transaction_price = purchase_price * Decimal(str(random.uniform(0.9, 1.1))).quantize(Decimal('0.01'))
                    transaction_quantity = Decimal(str(random.randint(1, 10) + random.random())).quantize(Decimal('0.01'))
                    
                    InvestmentTransaction.objects.create(
                        investment=investment,
                        transaction_type=transaction_type,
                        date=transaction_date,
                        price=transaction_price,
                        quantity=transaction_quantity,
                        fees=Decimal(str(random.randint(5, 20))),
                        notes=f"{transaction_type.capitalize()} transaction"
                    )
            self.stdout.write(self.style.SUCCESS('Created investments and transactions'))
        
        # Create credit factors if they don't exist
        credit_factors = [
            {'name': 'Payment History', 'description': 'Your history of paying bills on time', 'weight': 35},
            {'name': 'Credit Utilization', 'description': 'How much of your available credit you are using', 'weight': 30},
            {'name': 'Credit History Length', 'description': 'How long you have had credit accounts', 'weight': 15},
            {'name': 'Credit Mix', 'description': 'The variety of credit accounts you have', 'weight': 10},
            {'name': 'New Credit Inquiries', 'description': 'How many times you have applied for new credit recently', 'weight': 10}
        ]
        
        for factor in credit_factors:
            CreditFactor.objects.get_or_create(
                name=factor['name'],
                defaults={
                    'description': factor['description'],
                    'weight': factor['weight']
                }
            )
        self.stdout.write(self.style.SUCCESS('Created credit factors'))
        
        # Create credit history
        if CreditHistory.objects.filter(user=demo_user).count() < 6:
            credit_score = random.randint(650, 800)
            
            # Create credit history entries for the past 6 months
            for i in range(6):
                history_date = timezone.now().date() - timedelta(days=30 * (i + 1))
                history_score = credit_score - random.randint(-20, 20)
                
                credit_history = CreditHistory.objects.create(
                    user=demo_user,
                    date=history_date,
                    score=history_score,
                    report_source="FinWise Credit Bureau",
                    notes="Monthly credit report"
                )
                
                # Add factor scores for each credit history
                factors = CreditFactor.objects.all()
                for factor in factors:
                    factor_score = random.randint(60, 95)
                    CreditFactorScore.objects.create(
                        credit_history=credit_history,
                        factor=factor,
                        score=factor_score,
                        notes=f"Your {factor.name.lower()} is in good standing."
                    )
            
            self.stdout.write(self.style.SUCCESS('Created credit history and factor scores'))
        
        # Create credit estimation
        if not CreditEstimation.objects.filter(user=demo_user).exists():
            # Create a credit estimation with realistic values
            credit_estimation = CreditEstimation.objects.create(
                user=demo_user,
                missed_payments_count=random.randint(0, 2),
                late_payments_count=random.randint(0, 3),
                on_time_payments_streak=random.randint(10, 36),
                total_credit_limit=Decimal(str(random.randint(50000, 150000))),
                current_credit_usage=Decimal(str(random.randint(5000, 30000))),
                oldest_account_years=random.randint(3, 15),
                average_account_age_years=Decimal(str(random.randint(2, 10) + random.random())).quantize(Decimal('0.1')),
                has_credit_cards=True,
                has_installment_loans=True,
                has_mortgage=random.choice([True, False]),
                has_retail_accounts=random.choice([True, False]),
                recent_inquiries_count=random.randint(0, 3),
                new_accounts_last_year=random.randint(0, 2),
                estimated_score=random.randint(650, 800),
                confidence_level=random.randint(70, 95)
            )
            
            # Add improvement suggestions
            improvement_suggestions = [
                {
                    'title': 'Reduce Credit Card Balances',
                    'description': 'Pay down your credit card balances to reduce your credit utilization ratio.',
                    'impact': 'high',
                    'potential_points_gain': random.randint(20, 50),
                    'timeframe_months': 3
                },
                {
                    'title': 'Make All Payments On Time',
                    'description': 'Ensure all your payments are made on time to improve your payment history.',
                    'impact': 'high',
                    'potential_points_gain': random.randint(30, 60),
                    'timeframe_months': 6
                },
                {
                    'title': 'Avoid New Credit Applications',
                    'description': 'Limit new credit applications to reduce hard inquiries on your credit report.',
                    'impact': 'medium',
                    'potential_points_gain': random.randint(10, 25),
                    'timeframe_months': 3
                }
            ]
            
            for suggestion in improvement_suggestions:
                ImprovementSuggestion.objects.create(
                    credit_estimation=credit_estimation,
                    title=suggestion['title'],
                    description=suggestion['description'],
                    impact=suggestion['impact'],
                    potential_points_gain=suggestion['potential_points_gain'],
                    timeframe_months=suggestion['timeframe_months']
                )
            
            self.stdout.write(self.style.SUCCESS('Created credit estimation and improvement suggestions'))
        
        self.stdout.write(self.style.SUCCESS('Sample data creation complete!'))
