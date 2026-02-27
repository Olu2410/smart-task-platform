from django.urls import path
from . import views

app_name = 'ai_coach'

urlpatterns = [
    path('suggestions/', views.ai_suggestions, name='ai_suggestions'),
    path('suggestions/apply/<int:suggestion_id>/', views.apply_suggestion, name='apply_suggestion'),
    path('suggestions/dismiss/<int:suggestion_id>/', views.dismiss_suggestion, name='dismiss_suggestion'),
    path('analyze-task/<int:task_id>/', views.analyze_task, name='analyze_task'),
    path('weekly-plan/', views.generate_weekly_plan, name='generate_weekly_plan'),
    path('workload-analysis/', views.workload_analysis, name='workload_analysis'),
    path('analyze-all-tasks/', views.analyze_all_tasks, name='analyze_all_tasks'),
    path('ai-settings/', views.ai_settings, name='ai_settings'),
    path('settings/reset/', views.reset_ai_data, name='reset_ai_data'),
]
