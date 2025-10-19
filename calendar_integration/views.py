from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def calendar_view(request):
    return render(request, 'calendar_integration/calendar_view.html')

@login_required
def google_calendar_sync(request):
    return render(request, 'calendar_integration/sync_google.html')

@login_required
def oauth2callback(request):
    return render(request, 'calendar_integration/oauth_callback.html')

@login_required
def sync_settings(request):
    return render(request, 'calendar_integration/sync_settings.html')

@login_required
def calendar_events(request):
    return render(request, 'calendar_integration/events.html')

@login_required
def create_calendar_event(request):
    return render(request, 'calendar_integration/create_event.html')