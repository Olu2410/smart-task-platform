# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from tasks.models import Task
from .models import AISuggestion
from .services import AICoachService

@login_required
def ai_suggestions(request):
    """Display AI suggestions for the user's tasks"""
    suggestions = AISuggestion.objects.filter(
        task__assigned_to=request.user,
        is_applied=False
    ).select_related('task').order_by('-confidence_score')[:10]
    
    return render(request, 'ai_coach/suggestions.html', {
        'suggestions': suggestions
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
    
    return redirect('ai_suggestions')

@login_required
def dismiss_suggestion(request, suggestion_id):
    """Dismiss an AI suggestion"""
    suggestion = get_object_or_404(AISuggestion, id=suggestion_id, task__assigned_to=request.user)
    suggestion.delete()
    messages.info(request, 'Suggestion dismissed.')
    
    return redirect('ai_suggestions')

@login_required
def analyze_task(request, task_id):
    """Get AI analysis for a specific task"""
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    ai_service = AICoachService()
    analysis = ai_service.analyze_task_priority(task)
    
    return JsonResponse({
        'success': True,
        'analysis': analysis
    })

@login_required
def generate_weekly_plan(request):
    """Generate AI-powered weekly plan"""
    ai_service = AICoachService()
    weekly_plan = ai_service.generate_weekly_plan(request.user)
    
    return render(request, 'ai_coach/weekly_plan.html', {
        'weekly_plan': weekly_plan
    })

@login_required
def workload_analysis(request):
    """Get workload analysis for the team"""
    ai_service = AICoachService()
    analysis = ai_service.analyze_team_workload(request.user)
    
    return render(request, 'ai_coach/workload_analysis.html', {
        'analysis': analysis
    })