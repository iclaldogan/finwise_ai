#!/usr/bin/env python
"""
FinWise AI için zengin test verileri ekleme scripti
"""
import os
import sys
import django
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

# Django setup
sys.path.append('/home/ubuntu/finwise_deploy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.contrib.auth.models import User
from expenses.models import Expense, ExpenseCategory
from loans.models import Loan, LoanPayment
from goals.models import SavingsGoal, GoalContribution
from investments.models import Investment, InvestmentType, InvestmentTransaction

def create_demo_user():
    """Demo kullanıcı oluştur veya mevcut olanı al"""
    user, created = User.objects.get_or_create(
        username='demo@finwise.app',
        defaults={
            'email': 'demo@finwise.app',
            'first_name': 'Demo',
            'last_name': 'User',
            'is_active': True
        }
    )
    if created:
        user.set_password('demopass123')
        user.save()
        print(f"✅ Demo kullanıcı oluşturuldu: {user.username}")
    else:
        print(f"✅ Demo kullanıcı mevcut: {user.username}")
    return user

def create_expense_categories():
    """Gider kategorileri oluştur"""
    categories = [
        'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
        'Bills & Utilities', 'Healthcare', 'Education', 'Travel',
        'Personal Care', 'Home & Garden', 'Insurance', 'Taxes',
        'Gifts & Donations', 'Business Services', 'Fees & Charges'
    ]
    
    created_categories = []
    for cat_name in categories:
        category, created = ExpenseCategory.objects.get_or_create(
            name=cat_name,
            defaults={'description': f'{cat_name} related expenses'}
        )
        created_categories.append(category)
        if created:
            print(f"✅ Kategori oluşturuldu: {cat_name}")
    
    return created_categories

def create_expenses(user, categories):
    """Zengin gider verileri oluştur"""
    print("📊 Gider verileri oluşturuluyor...")
    
    # Son 6 ay için giderler
    base_date = datetime.now().date()
    expenses_data = [
        # Aylık sabit giderler
        ('Kira', 'Bills & Utilities', 2500, 'monthly'),
        ('Elektrik Faturası', 'Bills & Utilities', 180, 'monthly'),
        ('Su Faturası', 'Bills & Utilities', 85, 'monthly'),
        ('İnternet', 'Bills & Utilities', 89, 'monthly'),
        ('Telefon', 'Bills & Utilities', 120, 'monthly'),
        ('Sigorta', 'Insurance', 350, 'monthly'),
        
        # Haftalık giderler
        ('Market Alışverişi', 'Food & Dining', 450, 'weekly'),
        ('Benzin', 'Transportation', 280, 'weekly'),
        ('Kahve', 'Food & Dining', 85, 'weekly'),
        
        # Günlük giderler
        ('Öğle Yemeği', 'Food & Dining', 45, 'daily'),
        ('Ulaşım', 'Transportation', 25, 'daily'),
        ('Atıştırmalık', 'Food & Dining', 15, 'daily'),
        
        # Düzensiz giderler
        ('Sinema', 'Entertainment', 120, 'irregular'),
        ('Kitap', 'Education', 65, 'irregular'),
        ('Giyim', 'Shopping', 350, 'irregular'),
        ('Restoran', 'Food & Dining', 180, 'irregular'),
        ('Hediye', 'Gifts & Donations', 150, 'irregular'),
        ('Kuaför', 'Personal Care', 120, 'irregular'),
        ('Eczane', 'Healthcare', 85, 'irregular'),
        ('Taksi', 'Transportation', 45, 'irregular'),
    ]
    
    created_count = 0
    
    for expense_name, category_name, base_amount, frequency in expenses_data:
        category = next((c for c in categories if c.name == category_name), categories[0])
        
        # Son 6 ay için giderler oluştur
        for month_offset in range(6):
            current_date = base_date - timedelta(days=month_offset * 30)
            
            if frequency == 'monthly':
                # Aylık giderler - her ay 1 kez
                amount = base_amount + random.randint(-50, 50)
                Expense.objects.get_or_create(
                    user=user,
                    description=expense_name,
                    amount=Decimal(str(amount)),
                    category=category,
                    date=current_date,
                    defaults={'is_recurring': True, 'recurring_frequency': 'monthly'}
                )
                created_count += 1
                
            elif frequency == 'weekly':
                # Haftalık giderler - ayda 4 kez
                for week in range(4):
                    week_date = current_date - timedelta(days=week * 7)
                    amount = base_amount + random.randint(-30, 30)
                    Expense.objects.get_or_create(
                        user=user,
                        description=f"{expense_name} - Hafta {week+1}",
                        amount=Decimal(str(amount)),
                        category=category,
                        date=week_date,
                        defaults={'is_recurring': True, 'recurring_frequency': 'weekly'}
                    )
                    created_count += 1
                    
            elif frequency == 'daily':
                # Günlük giderler - ayda 20 iş günü
                for day in range(20):
                    day_date = current_date - timedelta(days=day)
                    amount = base_amount + random.randint(-10, 10)
                    Expense.objects.get_or_create(
                        user=user,
                        description=f"{expense_name} - {day_date.strftime('%d/%m')}",
                        amount=Decimal(str(amount)),
                        category=category,
                        date=day_date,
                        defaults={'is_recurring': True, 'recurring_frequency': 'daily'}
                    )
                    created_count += 1
                    
            elif frequency == 'irregular':
                # Düzensiz giderler - ayda 1-3 kez rastgele
                times = random.randint(1, 3)
                for _ in range(times):
                    random_day = random.randint(1, 28)
                    irregular_date = current_date.replace(day=random_day)
                    amount = base_amount + random.randint(-50, 100)
                    Expense.objects.get_or_create(
                        user=user,
                        description=f"{expense_name} - {irregular_date.strftime('%d/%m')}",
                        amount=Decimal(str(amount)),
                        category=category,
                        date=irregular_date,
                        defaults={'is_recurring': False}
                    )
                    created_count += 1
    
    print(f"✅ {created_count} gider kaydı oluşturuldu")

def create_loans(user):
    """Kredi verileri oluştur"""
    print("🏦 Kredi verileri oluşturuluyor...")
    
    loans_data = [
        {
            'loan_type': 'personal',
            'amount': Decimal('25000'),
            'interest_rate': Decimal('8.5'),
            'term_months': 48,
            'description': 'Ev tadilatı için kişisel kredi',
            'lender': 'ABC Bank'
        },
        {
            'loan_type': 'auto',
            'amount': Decimal('180000'),
            'interest_rate': Decimal('12.5'),
            'term_months': 60,
            'description': '2022 Model Otomobil Kredisi',
            'lender': 'XYZ Finans'
        },
        {
            'loan_type': 'mortgage',
            'amount': Decimal('450000'),
            'interest_rate': Decimal('15.8'),
            'term_months': 240,
            'description': 'Ev satın alma kredisi',
            'lender': 'DEF Mortgage'
        },
        {
            'loan_type': 'education',
            'amount': Decimal('35000'),
            'interest_rate': Decimal('6.5'),
            'term_months': 36,
            'description': 'Yüksek lisans eğitim kredisi',
            'lender': 'Eğitim Bankası'
        }
    ]
    
    created_count = 0
    for loan_data in loans_data:
        loan, created = Loan.objects.get_or_create(
            user=user,
            loan_type=loan_data['loan_type'],
            amount=loan_data['amount'],
            defaults={
                'interest_rate': loan_data['interest_rate'],
                'term_months': loan_data['term_months'],
                'description': loan_data['description'],
                'lender': loan_data['lender'],
                'start_date': datetime.now().date() - timedelta(days=random.randint(30, 365)),
                'status': 'active'
            }
        )
        
        if created:
            created_count += 1
            
            # Her kredi için ödeme geçmişi oluştur
            payments_made = random.randint(3, 12)
            for i in range(payments_made):
                payment_date = loan.start_date + timedelta(days=30 * i)
                monthly_payment = loan.amount / loan.term_months
                
                LoanPayment.objects.get_or_create(
                    loan=loan,
                    payment_date=payment_date,
                    defaults={
                        'amount': monthly_payment + Decimal(str(random.randint(-50, 50))),
                        'payment_type': 'regular'
                    }
                )
    
    print(f"✅ {created_count} kredi kaydı oluşturuldu")

def create_goals(user):
    """Hedef verileri oluştur"""
    print("🎯 Hedef verileri oluşturuluyor...")
    
    goals_data = [
        {
            'name': 'Acil Durum Fonu',
            'description': '6 aylık gider karşılığı acil durum fonu oluşturma',
            'target_amount': Decimal('45000'),
            'current_amount': Decimal('18500'),
            'target_date': date.today() + timedelta(days=365),
            'priority': 'high',
            'status': 'active'
        },
        {
            'name': 'Yeni Araba',
            'description': '2024 model hibrit araç için birikim',
            'target_amount': Decimal('250000'),
            'current_amount': Decimal('85000'),
            'target_date': date.today() + timedelta(days=730),
            'priority': 'medium',
            'status': 'active'
        },
        {
            'name': 'Tatil Fonu',
            'description': 'Avrupa turu için tatil bütçesi',
            'target_amount': Decimal('15000'),
            'current_amount': Decimal('12800'),
            'target_date': date.today() + timedelta(days=180),
            'priority': 'low',
            'status': 'active'
        },
        {
            'name': 'Ev Peşinatı',
            'description': 'İlk ev satın alma için peşinat birikimi',
            'target_amount': Decimal('120000'),
            'current_amount': Decimal('35000'),
            'target_date': date.today() + timedelta(days=1095),
            'priority': 'high',
            'status': 'active'
        },
        {
            'name': 'Emeklilik Fonu',
            'description': 'Uzun vadeli emeklilik birikimi',
            'target_amount': Decimal('500000'),
            'current_amount': Decimal('125000'),
            'target_date': date.today() + timedelta(days=7300),
            'priority': 'medium',
            'status': 'active'
        }
    ]
    
    created_count = 0
    for goal_data in goals_data:
        goal, created = SavingsGoal.objects.get_or_create(
            user=user,
            name=goal_data['name'],
            defaults=goal_data
        )
        
        if created:
            created_count += 1
            
            # Her hedef için katkı geçmişi oluştur
            contributions_made = random.randint(5, 15)
            total_contributed = Decimal('0')
            
            for i in range(contributions_made):
                contribution_date = date.today() - timedelta(days=random.randint(1, 365))
                contribution_amount = Decimal(str(random.randint(500, 5000)))
                
                if total_contributed + contribution_amount <= goal.current_amount:
                    GoalContribution.objects.get_or_create(
                        goal=goal,
                        date=contribution_date,
                        defaults={'amount': contribution_amount}
                    )
                    total_contributed += contribution_amount
    
    print(f"✅ {created_count} hedef kaydı oluşturuldu")

def create_investment_types():
    """Yatırım türleri oluştur"""
    investment_types_data = [
        {'name': 'Hisse Senedi', 'category': 'stocks', 'description': 'Borsa İstanbul hisse senetleri'},
        {'name': 'Devlet Tahvili', 'category': 'bonds', 'description': 'Türkiye Cumhuriyeti tahvilleri'},
        {'name': 'Altın', 'category': 'commodities', 'description': 'Fiziksel altın yatırımı'},
        {'name': 'Döviz', 'category': 'forex', 'description': 'Yabancı para yatırımı'},
        {'name': 'Kripto Para', 'category': 'crypto', 'description': 'Bitcoin ve diğer kripto paralar'},
        {'name': 'Gayrimenkul Fonu', 'category': 'real_estate', 'description': 'GYO yatırım fonları'},
        {'name': 'Banka Mevduatı', 'category': 'cash', 'description': 'Vadeli mevduat hesapları'},
    ]
    
    created_types = []
    for type_data in investment_types_data:
        inv_type, created = InvestmentType.objects.get_or_create(
            name=type_data['name'],
            defaults=type_data
        )
        created_types.append(inv_type)
        if created:
            print(f"✅ Yatırım türü oluşturuldu: {type_data['name']}")
    
    return created_types

def create_investments(user, investment_types):
    """Yatırım verileri oluştur"""
    print("📈 Yatırım verileri oluşturuluyor...")
    
    investments_data = [
        {
            'name': 'BIST 30 Endeks Fonu',
            'type': 'Hisse Senedi',
            'quantity': Decimal('1000'),
            'purchase_price': Decimal('12.50'),
            'current_price': Decimal('14.25'),
            'purchase_date': date.today() - timedelta(days=180)
        },
        {
            'name': 'Türkiye 5 Yıl Tahvil',
            'type': 'Devlet Tahvili',
            'quantity': Decimal('50'),
            'purchase_price': Decimal('980'),
            'current_price': Decimal('1020'),
            'purchase_date': date.today() - timedelta(days=365)
        },
        {
            'name': 'Gram Altın',
            'type': 'Altın',
            'quantity': Decimal('25'),
            'purchase_price': Decimal('1850'),
            'current_price': Decimal('1920'),
            'purchase_date': date.today() - timedelta(days=90)
        },
        {
            'name': 'USD/TRY',
            'type': 'Döviz',
            'quantity': Decimal('5000'),
            'purchase_price': Decimal('28.50'),
            'current_price': Decimal('30.25'),
            'purchase_date': date.today() - timedelta(days=120)
        },
        {
            'name': 'Bitcoin',
            'type': 'Kripto Para',
            'quantity': Decimal('0.5'),
            'purchase_price': Decimal('1200000'),
            'current_price': Decimal('1350000'),
            'purchase_date': date.today() - timedelta(days=60)
        },
        {
            'name': 'İş GYO',
            'type': 'Gayrimenkul Fonu',
            'quantity': Decimal('2000'),
            'purchase_price': Decimal('8.75'),
            'current_price': Decimal('9.40'),
            'purchase_date': date.today() - timedelta(days=200)
        },
        {
            'name': 'Vadeli Mevduat',
            'type': 'Banka Mevduatı',
            'quantity': Decimal('1'),
            'purchase_price': Decimal('50000'),
            'current_price': Decimal('52500'),
            'purchase_date': date.today() - timedelta(days=150)
        }
    ]
    
    created_count = 0
    for inv_data in investments_data:
        inv_type = next((t for t in investment_types if t.name == inv_data['type']), investment_types[0])
        
        investment, created = Investment.objects.get_or_create(
            user=user,
            name=inv_data['name'],
            investment_type=inv_type,
            defaults={
                'quantity': inv_data['quantity'],
                'purchase_price': inv_data['purchase_price'],
                'current_value': inv_data['quantity'] * inv_data['current_price'],
                'purchase_date': inv_data['purchase_date'],
                'status': 'active'
            }
        )
        
        if created:
            created_count += 1
            
            # Her yatırım için işlem geçmişi oluştur
            transactions_count = random.randint(1, 5)
            for i in range(transactions_count):
                transaction_date = inv_data['purchase_date'] + timedelta(days=random.randint(1, 30))
                
                InvestmentTransaction.objects.get_or_create(
                    investment=investment,
                    transaction_type='buy',
                    date=transaction_date,
                    defaults={
                        'price': inv_data['purchase_price'] + Decimal(str(random.randint(-100, 100))),
                        'quantity': Decimal(str(random.randint(10, 100))),
                        'fees': Decimal(str(random.randint(5, 25)))
                    }
                )
    
    print(f"✅ {created_count} yatırım kaydı oluşturuldu")

def main():
    """Ana fonksiyon"""
    print("🚀 FinWise AI Test Verileri Ekleniyor...")
    print("=" * 50)
    
    # Demo kullanıcı oluştur
    user = create_demo_user()
    
    # Kategoriler oluştur
    categories = create_expense_categories()
    
    # Test verilerini oluştur
    create_expenses(user, categories)
    create_loans(user)
    create_goals(user)
    
    # Yatırım türleri ve yatırımlar
    investment_types = create_investment_types()
    create_investments(user, investment_types)
    
    print("=" * 50)
    print("🎉 Tüm test verileri başarıyla eklendi!")
    print(f"👤 Kullanıcı: {user.username}")
    print(f"💰 Giderler: {Expense.objects.filter(user=user).count()} kayıt")
    print(f"🏦 Krediler: {Loan.objects.filter(user=user).count()} kayıt")
    print(f"🎯 Hedefler: {SavingsGoal.objects.filter(user=user).count()} kayıt")
    print(f"📈 Yatırımlar: {Investment.objects.filter(user=user).count()} kayıt")

if __name__ == '__main__':
    main()

