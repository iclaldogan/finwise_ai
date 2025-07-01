from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('', views.loan_home, name='loan_home'),
    path('list/', views.loan_list, name='loan_list'),
    path('create/', views.loan_create, name='loan_create'),
    path('<int:pk>/', views.loan_detail, name='loan_detail'),
    path('<int:pk>/edit/', views.loan_edit, name='loan_edit'),
    path('<int:pk>/delete/', views.loan_delete, name='loan_delete'),
    
    # Loan simulator
    path('simulator/', views.loan_simulator, name='loan_simulator'),
    path('simulation/<int:loan_id>/eligibility/<int:eligibility_id>/', views.loan_simulation_result, name='loan_simulation_result'),
    
    # Payments
    path('payments/<int:pk>/paid/', views.loan_payment_mark_paid, name='loan_payment_mark_paid'),
    
    # Eligibility
    path('eligibility-check/', views.loan_eligibility_check, name='loan_eligibility_check'),
    path('eligibility/<int:pk>/', views.loan_eligibility_result, name='loan_eligibility_result'),
] 