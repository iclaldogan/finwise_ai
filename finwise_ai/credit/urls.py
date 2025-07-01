from django.urls import path
from . import views

app_name = 'credit'

urlpatterns = [
    path('', views.credit_home, name='credit_home'),
    
    # Credit history
    path('history/', views.credit_history_list, name='credit_history_list'),
    path('history/add/', views.credit_history_add, name='credit_history_add'),
    path('history/<int:pk>/edit/', views.credit_history_edit, name='credit_history_edit'),
    path('history/<int:pk>/delete/', views.credit_history_delete, name='credit_history_delete'),
    
    # Credit estimation
    path('estimator/', views.credit_estimator, name='credit_estimator'),
    path('quick-estimator/', views.quick_credit_estimator, name='quick_credit_estimator'),
    path('estimation/<int:pk>/', views.credit_estimation_result, name='credit_estimation_result'),
    
    # Improvement suggestions
    path('suggestions/<int:pk>/implemented/', views.mark_suggestion_implemented, name='mark_suggestion_implemented'),
    
    # Analytics
    path('score-chart/', views.credit_score_chart, name='credit_score_chart'),
    path('score-comparison/', views.credit_score_comparison, name='credit_score_comparison'),
] 