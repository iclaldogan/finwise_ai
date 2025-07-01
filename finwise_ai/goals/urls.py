from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('', views.goals_home, name='goals_home'),
    path('list/', views.goal_list, name='goal_list'),
    path('create/', views.goal_create, name='goal_create'),
    path('<int:pk>/', views.goal_detail, name='goal_detail'),
    path('<int:pk>/edit/', views.goal_edit, name='goal_edit'),
    path('<int:pk>/delete/', views.goal_delete, name='goal_delete'),
    
    # Contributions
    path('<int:goal_id>/contribute/', views.contribution_add, name='contribution_add'),
    path('contributions/<int:pk>/delete/', views.contribution_delete, name='contribution_delete'),
    
    # Milestones
    path('<int:goal_id>/milestones/add/', views.milestone_add, name='milestone_add'),
    path('milestones/<int:pk>/edit/', views.milestone_edit, name='milestone_edit'),
    path('milestones/<int:pk>/delete/', views.milestone_delete, name='milestone_delete'),
    
    # Planning
    path('savings-plan/', views.savings_plan, name='savings_plan'),
    
    # API endpoints
    path('<int:pk>/progress-chart/', views.goal_progress_chart, name='goal_progress_chart'),
] 