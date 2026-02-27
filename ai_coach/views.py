from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q
from tasks.models import Task, Project
from users.models import Team
from .models import AISuggestion
from .services import AICoachService

@login_required
def ai_suggestions(request):
    """Display AI suggestions for the user's tasks"""
    # Get suggestions for user's tasks
    suggestions = AISuggestion.objects.filter(
        task__assigned_to=request.user,
        is_applied=False
    ).select_related('task', 'task__project').order_by('-confidence_score', '-created_at')
    
    # Get task-specific suggestions
    user_tasks = Task.objects.filter(assigned_to=request.user, status__in=['todo', 'in_progress'])
    
    return render(request, 'ai_coach/suggestions.html', {
        'suggestions': suggestions,
        'user_tasks': user_tasks
    })

@login_required
def apply_suggestion(request, suggestion_id):
    """Apply an AI suggestion to a task"""
    suggestion = get_object_or_404(AISuggestion, id=suggestion_id, task__assigned_to=request.user)
    
    ai_service = AICoachService()
    success = ai_service.apply_suggestion(suggestion)
    
    if success:
        suggestion.is_applied = True
        suggestion.save()
        messages.success(request, 'AI suggestion applied successfully!')
    else:
        messages.error(request, 'Failed to apply AI suggestion.')
    
    return redirect('ai_coach:ai_suggestions')

@login_required
def dismiss_suggestion(request, suggestion_id):
    """Dismiss an AI suggestion"""
    suggestion = get_object_or_404(AISuggestion, id=suggestion_id, task__assigned_to=request.user)
    suggestion.delete()
    messages.info(request, 'Suggestion dismissed.')
    
    return redirect('ai_coach:ai_suggestions')

@login_required
def analyze_task(request, task_id):
    """Get AI analysis for a specific task"""
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    ai_service = AICoachService()
    
    analysis_type = request.GET.get('type', 'priority')
    
    if analysis_type == 'priority':
        result = ai_service.analyze_task_priority(task)
    elif analysis_type == 'timing':
        result = ai_service.suggest_task_timing(task, request.user)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid analysis type'})
    
    return JsonResponse(result)

# @login_required
# def analyze_task(request, task_id):
#     """Get AI analysis for a specific task"""
#     task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
#     ai_service = AICoachService()
#     analysis = ai_service.analyze_task_priority(task)
    
#     return JsonResponse({
#         'success': True,
#         'analysis': analysis
#     })

@login_required
def generate_weekly_plan(request):
    """Generate AI-powered weekly plan"""
    ai_service = AICoachService()
    weekly_plan = ai_service.generate_weekly_plan(request.user)
    
    # Get user's upcoming tasks for context
    upcoming_tasks = Task.objects.filter(
        assigned_to=request.user,
        status__in=['todo', 'in_progress'],
        due_date__lte=timezone.now() + timedelta(days=14)
    ).select_related('project').order_by('due_date', '-priority')
    
    return render(request, 'ai_coach/weekly_plan.html', {
        'weekly_plan': weekly_plan,
        'upcoming_tasks': upcoming_tasks
    })

@login_required
def workload_analysis(request):
    """Get workload analysis for user's teams"""
    user_teams = Team.objects.filter(members=request.user)
    selected_team_id = request.GET.get('team_id')
    
    if selected_team_id:
        team = get_object_or_404(Team, id=selected_team_id, members=request.user)
    else:
        team = user_teams.first()
    
    analysis = None
    if team:
        ai_service = AICoachService()
        analysis = ai_service.analyze_workload_balance(team)
    
    # Get team workload statistics
    team_stats = []
    for user_team in user_teams:
        members_data = []
        for member in user_team.members.all():
            tasks = Task.objects.filter(
                assigned_to=member,
                project__team=user_team,
                status__in=['todo', 'in_progress']
            )
            members_data.append({
                'member': member,
                'total_tasks': tasks.count(),
                'high_priority': tasks.filter(priority__in=['high', 'urgent']).count(),
                'overdue': tasks.filter(due_date__lt=timezone.now()).count()
            })
        team_stats.append({
            'team': user_team,
            'members': members_data
        })
    
    return render(request, 'ai_coach/workload_analysis.html', {
        'analysis': analysis,
        'teams': user_teams,
        'selected_team': team,
        'team_stats': team_stats
    })

@login_required
def analyze_all_tasks(request):
    """Trigger AI analysis for all user's tasks"""
    user_tasks = Task.objects.filter(
        assigned_to=request.user,
        status__in=['todo', 'in_progress'],
        due_date__isnull=False
    )[:10]  # Limit to prevent abuse
    
    ai_service = AICoachService()
    results = []
    
    for task in user_tasks:
        # Only analyze if no recent suggestions exist
        recent_suggestions = AISuggestion.objects.filter(
            task=task,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).exists()
        
        if not recent_suggestions:
            result = ai_service.analyze_task_priority(task)
            results.append({
                'task': task.title,
                'success': result.get('success', False)
            })
    
    messages.success(request, f'AI analysis completed for {len(results)} tasks.')
    return redirect('ai_coach:ai_suggestions')

# @login_required
# def ai_settings(request):
#     """AI preferences settings"""
#     if request.method == 'POST':
#         user = request.user
#         user.ai_task_suggestions = request.POST.get('ai_task_suggestions') == 'on'
#         user.ai_time_optimization = request.POST.get('ai_time_optimization') == 'on'
#         user.save()
#         messages.success(request, 'AI preferences updated!')
#         return redirect('ai_coach:ai_settings')
    
#     return render(request, 'ai_coach/settings.html')

@login_required
def ai_settings(request):
    """AI preferences settings"""
    # Get AI usage statistics
    ai_suggestions_count = AISuggestion.objects.filter(
        task__assigned_to=request.user
    ).count()
    
    applied_suggestions_count = AISuggestion.objects.filter(
        task__assigned_to=request.user,
        is_applied=True
    ).count()
    
    analyzed_tasks_count = Task.objects.filter(
        assigned_to=request.user,
        aisuggestion__isnull=False
    ).distinct().count()
    
    # Calculate acceptance rate
    if ai_suggestions_count > 0:
        acceptance_rate = round((applied_suggestions_count / ai_suggestions_count) * 100)
    else:
        acceptance_rate = 0
    
    if request.method == 'POST':
        user = request.user
        user.ai_task_suggestions = request.POST.get('ai_task_suggestions') == 'on'
        user.ai_time_optimization = request.POST.get('ai_time_optimization') == 'on'
        user.save()
        messages.success(request, 'AI preferences updated!')
        return redirect('ai_coach:ai_settings')
    
    # Check if OpenAI is configured
    openai_configured = bool(settings.OPENAI_API_KEY)
    
    return render(request, 'ai_coach/settings.html', {
        'ai_suggestions_count': ai_suggestions_count,
        'applied_suggestions_count': applied_suggestions_count,
        'analyzed_tasks_count': analyzed_tasks_count,
        'acceptance_rate': acceptance_rate,
        'openai_configured': openai_configured,
    })

@login_required
def reset_ai_data(request):
    """Reset all AI data for the user"""
    if request.method == 'POST':
        # Delete all AI suggestions for user's tasks
        deleted_count = AISuggestion.objects.filter(
            task__assigned_to=request.user
        ).delete()[0]
        
        messages.success(request, f'Reset complete! Removed {deleted_count} AI suggestions.')
        return redirect('ai_coach:ai_settings')
    
    return redirect('ai_coach:ai_settings')




# # Create your views here.
# from datetime import timedelta
# from django.utils import timezone
# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib.auth.decorators import login_required
# from django.http import JsonResponse
# from django.contrib import messages
# from core import settings
# from tasks.models import Task
# from .models import AISuggestion
# from .services import AICoachService

# @login_required
# def ai_suggestions(request):
#     """Display AI suggestions for the user's tasks"""
#     suggestions = AISuggestion.objects.filter(
#         task__assigned_to=request.user,
#         is_applied=False
#     ).select_related('task').order_by('-confidence_score')[:10]
    
#     return render(request, 'ai_coach/suggestions.html', {
#         'suggestions': suggestions
#     })

# @login_required
# def apply_suggestion(request, suggestion_id):
#     """Apply an AI suggestion to a task"""
#     suggestion = get_object_or_404(AISuggestion, id=suggestion_id, task__assigned_to=request.user)
    
#     ai_service = AICoachService()
#     success = ai_service.apply_suggestion(suggestion)
    
#     if success:
#         suggestion.is_applied = True
#         suggestion.save()
#         messages.success(request, 'AI suggestion applied successfully!')
#     else:
#         messages.error(request, 'Failed to apply AI suggestion.')
    
#     return redirect('ai_suggestions')

# @login_required
# def dismiss_suggestion(request, suggestion_id):
#     """Dismiss an AI suggestion"""
#     suggestion = get_object_or_404(AISuggestion, id=suggestion_id, task__assigned_to=request.user)
#     suggestion.delete()
#     messages.info(request, 'Suggestion dismissed.')
    
#     return redirect('ai_suggestions')

# @login_required
# def analyze_task(request, task_id):
#     """Get AI analysis for a specific task"""
#     task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
#     ai_service = AICoachService()
#     analysis = ai_service.analyze_task_priority(task)
    
#     return JsonResponse({
#         'success': True,
#         'analysis': analysis
#     })

# @login_required
# def generate_weekly_plan(request):
#     """Generate AI-powered weekly plan"""
#     ai_service = AICoachService()
#     weekly_plan = ai_service.generate_weekly_plan(request.user)
    
#     return render(request, 'ai_coach/weekly_plan.html', {
#         'weekly_plan': weekly_plan
#     })

# @login_required
# def workload_analysis(request):
#     """Get workload analysis for the team"""
#     ai_service = AICoachService()
#     analysis = ai_service.analyze_team_workload(request.user)
    
#     return render(request, 'ai_coach/workload_analysis.html', {
#         'analysis': analysis
#     })

# #Extras from commented codes above

# @login_required
# def analyze_all_tasks(request):
#     """Trigger AI analysis for all user's tasks"""
#     user_tasks = Task.objects.filter(
#         assigned_to=request.user,
#         status__in=['todo', 'in_progress'],
#         due_date__isnull=False
#     )[:10]  # Limit to prevent abuse
    
#     ai_service = AICoachService()
#     results = []
    
#     for task in user_tasks:
#         # Only analyze if no recent suggestions exist
#         recent_suggestions = AISuggestion.objects.filter(
#             task=task,
#             created_at__gte=timezone.now() - timedelta(hours=24)
#         ).exists()
        
#         if not recent_suggestions:
#             result = ai_service.analyze_task_priority(task)
#             results.append({
#                 'task': task.title,
#                 'success': result.get('success', False)
#             })
    
#     messages.success(request, f'AI analysis completed for {len(results)} tasks.')
#     return redirect('ai_coach:ai_suggestions')

# @login_required
# def ai_settings(request):
#     """AI preferences settings"""
#     # Get AI usage statistics
#     ai_suggestions_count = AISuggestion.objects.filter(
#         task__assigned_to=request.user
#     ).count()
    
#     applied_suggestions_count = AISuggestion.objects.filter(
#         task__assigned_to=request.user,
#         is_applied=True
#     ).count()
    
#     analyzed_tasks_count = Task.objects.filter(
#         assigned_to=request.user,
#         aisuggestion__isnull=False
#     ).distinct().count()
    
#     # Calculate acceptance rate
#     if ai_suggestions_count > 0:
#         acceptance_rate = round((applied_suggestions_count / ai_suggestions_count) * 100)
#     else:
#         acceptance_rate = 0
    
#     if request.method == 'POST':
#         user = request.user
#         user.ai_task_suggestions = request.POST.get('ai_task_suggestions') == 'on'
#         user.ai_time_optimization = request.POST.get('ai_time_optimization') == 'on'
#         user.save()
#         messages.success(request, 'AI preferences updated!')
#         return redirect('ai_coach:ai_settings')
    
#     # Check if OpenAI is configured
#     openai_configured = bool(settings.OPENAI_API_KEY)
    
#     return render(request, 'ai_coach/settings.html', {
#         'ai_suggestions_count': ai_suggestions_count,
#         'applied_suggestions_count': applied_suggestions_count,
#         'analyzed_tasks_count': analyzed_tasks_count,
#         'acceptance_rate': acceptance_rate,
#         'openai_configured': openai_configured,
#     })

# @login_required
# def reset_ai_data(request):
#     """Reset all AI data for the user"""
#     if request.method == 'POST':
#         # Delete all AI suggestions for user's tasks
#         deleted_count = AISuggestion.objects.filter(
#             task__assigned_to=request.user
#         ).delete()[0]
        
#         messages.success(request, f'Reset complete! Removed {deleted_count} AI suggestions.')
#         return redirect('ai_coach:ai_settings')
    
#     return redirect('ai_coach:ai_settings')