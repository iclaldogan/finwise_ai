from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expense_home, name='expense_home'),
    path('list/', views.expense_list, name='expense_list'),
    path('create/', views.expense_create, name='expense_create'),
    path('<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Recurring expenses
    path('recurring/', views.recurring_expenses, name='recurring_expenses'),
    path('recurring/<int:pk>/edit/', views.recurring_expense_edit, name='recurring_expense_edit'),
    
    # Anomaly detection
    path('anomalies/', views.anomaly_detection, name='anomaly_detection'),
    path('anomalies/<int:pk>/reviewed/', views.mark_anomaly_reviewed, name='mark_anomaly_reviewed'),
    
    # Analytics
    path('analytics/', views.expense_analytics, name='expense_analytics'),
] 