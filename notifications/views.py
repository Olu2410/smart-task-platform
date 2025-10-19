from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def notifications_list(request):
    return render(request, 'notifications/notifications_list.html')

@login_required
def mark_notification_read(request, notification_id):
    return render(request, 'notifications/notifications_list.html')

@login_required
def mark_all_notifications_read(request):
    return render(request, 'notifications/notifications_list.html')

@login_required
def notification_settings(request):
    return render(request, 'notifications/settings.html')