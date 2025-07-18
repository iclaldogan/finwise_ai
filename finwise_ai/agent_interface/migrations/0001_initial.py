# Generated by Django 5.2.1 on 2025-05-23 14:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('credit', '0001_initial'),
        ('expenses', '0001_initial'),
        ('goals', '0001_initial'),
        ('investments', '0001_initial'),
        ('loans', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PromptTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('expense_analysis', 'Expense Analysis'), ('budget_planning', 'Budget Planning'), ('investment_advice', 'Investment Advice'), ('debt_management', 'Debt Management'), ('savings_strategy', 'Savings Strategy'), ('credit_improvement', 'Credit Improvement'), ('general', 'General Financial Advice')], max_length=20)),
                ('template_text', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_type', models.CharField(choices=[('user', 'User Message'), ('assistant', 'Assistant Message'), ('system', 'System Message')], max_length=10)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='agent_interface.conversation')),
                ('related_credit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='credit.creditestimation')),
                ('related_expense', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='expenses.expense')),
                ('related_goal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='goals.savingsgoal')),
                ('related_investment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='investments.investment')),
                ('related_loan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='loans.loan')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_text', models.TextField()),
                ('detected_intent', models.CharField(choices=[('expense_analysis', 'Expense Analysis'), ('budget_planning', 'Budget Planning'), ('investment_advice', 'Investment Advice'), ('debt_management', 'Debt Management'), ('savings_strategy', 'Savings Strategy'), ('credit_improvement', 'Credit Improvement'), ('general_question', 'General Question'), ('unknown', 'Unknown Intent')], default='unknown', max_length=20)),
                ('confidence_score', models.FloatField(default=0.0)),
                ('processed_successfully', models.BooleanField(default=False)),
                ('processing_time', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queries', to='agent_interface.conversation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='queries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Query',
                'verbose_name_plural': 'User Queries',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('data_retrieval', 'Data Retrieval'), ('calculation', 'Calculation'), ('recommendation', 'Recommendation'), ('notification', 'Notification'), ('goal_creation', 'Goal Creation'), ('expense_categorization', 'Expense Categorization'), ('other', 'Other Action')], max_length=25)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=15)),
                ('result', models.TextField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('user_query', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='agent_interface.userquery')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
