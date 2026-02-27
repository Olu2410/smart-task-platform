from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .services import ActivityQueryService

@login_required
def team_activity_feed(request, team_id):
    """Display activity feed for a team"""
    from users.models import Team
    team = get_object_or_404(Team, id=team_id, members=request.user)
    
    activities = ActivityQueryService.get_team_activities(team)
    
    return render(request, 'activity_feeds/team_activity_feed.html', {
        'team': team,
        'activities': activities,
    })

@login_required
def user_activity_feed(request):
    """Display activity feed for current user across all teams"""
    activities = ActivityQueryService.get_user_activities(request.user)
    
    return render(request, 'activity_feeds/user_activity_feed.html', {
        'activities': activities,
    })

@login_required
def activity_feed_api(request, team_id=None):
    """API endpoint for activity feed (AJAX)"""
    if team_id:
        from users.models import Team
        team = get_object_or_404(Team, id=team_id, members=request.user)
        activities = ActivityQueryService.get_team_activities(team)
    else:
        activities = ActivityQueryService.get_user_activities(request.user)
    
    activity_data = []
    for activity in activities:
        activity_data.append({
            'id': str(activity.id),
            'user': {
                'username': activity.user.username,
                'full_name': activity.user.get_full_name(),
            },
            'activity_type': activity.get_activity_type_display(),
            'description': activity.description,
            'created_at': activity.created_at.isoformat(),
            'is_recent': activity.is_recent,
        })
    
    return JsonResponse({'activities': activity_data})