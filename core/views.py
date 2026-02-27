from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from tasks.models import Task
from users.models import Team
from django.utils import timezone

def dashboard(request):
    """Dashboard view that handles both authenticated and anonymous users"""
    if not request.user.is_authenticated:
        # Show landing page for unauthenticated users
        return render(request, 'landing.html')
    
    # Get teams the user is member of
    user_teams = Team.objects.filter(members=request.user)
    
    # Get tasks organized by status for the dashboard
    tasks_by_status = {}
    for status_choice in Task.STATUS_CHOICES:
        status = status_choice[0]
        tasks = Task.objects.filter(
            project__team__in=user_teams,
            status=status
        ).select_related('assigned_to', 'project').order_by('order', '-priority')[:5]
        tasks_by_status[status] = tasks
    
    # Get statistics for dashboard
    total_tasks = Task.objects.filter(project__team__in=user_teams).count()
    pending_tasks = Task.objects.filter(
        project__team__in=user_teams,
        status__in=['todo', 'in_progress', 'review']
    ).count()
    completed_tasks = Task.objects.filter(
        project__team__in=user_teams,
        status='done'
    ).count()
    overdue_tasks = Task.objects.filter(
        project__team__in=user_teams,
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress', 'review']
    ).count()
    
    # Get recent activities from activity feeds
    recent_activities = []
    try:
        from activity_feeds.services import ActivityQueryService
        recent_activities = ActivityQueryService.get_user_activities(request.user, limit=5)
    except ImportError:
        # Activity feeds app not available yet, use empty list
        pass
    
    return render(request, 'dashboard.html', {
        'tasks_by_status': tasks_by_status,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_activities': recent_activities,
    })