from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('financial-summary/', views.financial_summary, name='financial_summary'),
    path('expense-trends/', views.expense_trends, name='expense_trends'),
    path('income-vs-expenses/', views.income_vs_expenses, name='income_vs_expenses'),
    path('net-worth-tracker/', views.net_worth_tracker, name='net_worth_tracker'),
    path('goals-progress/', views.financial_goals_progress, name='financial_goals_progress'),
    path('budget-performance/', views.budget_performance, name='budget_performance'),
    
    # API endpoints
    path('api/expense-breakdown/', views.dashboard_api_expense_breakdown, name='api_expense_breakdown'),
    path('api/weekly-spending/', views.dashboard_api_weekly_spending, name='api_weekly_spending'),
] 