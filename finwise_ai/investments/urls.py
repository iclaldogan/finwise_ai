from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.investments_home, name='investments_home'),
    path('list/', views.investment_list, name='investment_list'),
    path('create/', views.investment_create, name='investment_create'),
    path('<int:pk>/', views.investment_detail, name='investment_detail'),
    path('<int:pk>/edit/', views.investment_edit, name='investment_edit'),
    path('<int:pk>/delete/', views.investment_delete, name='investment_delete'),
    
    # Transactions
    path('<int:investment_id>/transactions/add/', views.transaction_add, name='transaction_add'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    
    # Investment types
    path('types/', views.investment_type_list, name='investment_type_list'),
    path('types/create/', views.investment_type_create, name='investment_type_create'),
    
    # Simulator
    path('simulator/', views.investment_simulator, name='investment_simulator'),
    path('simulation/<int:pk>/', views.investment_simulation_result, name='investment_simulation_result'),
    
    # Analysis
    path('compare-strategies/', views.compare_strategies, name='compare_strategies'),
    path('portfolio-analysis/', views.portfolio_analysis, name='portfolio_analysis'),
] 