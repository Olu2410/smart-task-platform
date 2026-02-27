
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import CalendarEvent, CalendarSync, TimeBlock, WorkingHours
from .services import GoogleCalendarService, CalendarManager
from tasks.models import Task



@login_required
def calendar_view(request):
    """Main calendar view"""
    calendar_manager = CalendarManager(request.user)
    
    # Get time range (default to current week)
    start_date_str = request.GET.get('start', '')
    view_type = request.GET.get('view', 'week')  # week, day, month
    
    now = timezone.now()
    
    if start_date_str:
        try:
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        except ValueError:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate date range based on view type
    date_range = []
    if view_type == 'day':
        date_range = [start_date]
        previous_date = start_date - timedelta(days=1)
        next_date = start_date + timedelta(days=1)
    elif view_type == 'week':
        # Start from Monday
        start_date = start_date - timedelta(days=start_date.weekday())
        date_range = [start_date + timedelta(days=i) for i in range(7)]
        previous_date = start_date - timedelta(days=7)
        next_date = start_date + timedelta(days=7)
    else:  # month
        # Start from first day of month
        start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get 35 days for calendar display (5 weeks)
        date_range = [start_date + timedelta(days=i) for i in range(35)]
        # Calculate next/previous months
        if start_date.month == 12:
            next_month = start_date.replace(year=start_date.year + 1, month=1)
        else:
            next_month = start_date.replace(month=start_date.month + 1)
        previous_date = start_date - timedelta(days=1)
        previous_date = previous_date.replace(day=1)
        next_date = next_month
    
    # Get events for the date range
    if date_range:
        events_start = date_range[0]
        events_end = date_range[-1] + timedelta(days=1)
        events = CalendarEvent.objects.filter(
            user=request.user,
            start_time__gte=events_start,
            start_time__lt=events_end
        ).order_by('start_time')
    else:
        events = CalendarEvent.objects.none()
    
    # Get today's events for sidebar
    todays_events = calendar_manager.get_todays_events()
    
    # Get unscheduled tasks
    unscheduled_tasks = Task.objects.filter(
        assigned_to=request.user,
        status__in=['todo', 'in_progress'],
        calendar_events__isnull=True
    )[:10]
    
    # Check Google Calendar sync status
    google_sync = CalendarSync.objects.filter(user=request.user, provider='google', is_active=True).first()
    
    context = {
        'events': events,
        'todays_events': todays_events,
        'unscheduled_tasks': unscheduled_tasks,
        'date_range': date_range,
        'start_date': start_date,
        'view_type': view_type,
        'google_sync': google_sync,
        'now': now,
        'previous_date': previous_date.strftime('%Y-%m-%d') if 'previous_date' in locals() else '',
        'next_date': next_date.strftime('%Y-%m-%d') if 'next_date' in locals() else '',
    }
    
    return render(request, 'calendar_integration/calendar_view.html', context)

# @login_required
# def calendar_view(request):
#     """Main calendar view"""
#     calendar_manager = CalendarManager(request.user)
    
#     # Get time range (default to current week)
#     start_date_str = request.GET.get('start', '')
#     view_type = request.GET.get('view', 'week')  # week, day, month
    
#     if start_date_str:
#         start_date = timezone.make_aware(datetime.fromisoformat(start_date_str))
#     else:
#         start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
#     # Calculate date range based on view type
#     if view_type == 'day':
#         end_date = start_date + timedelta(days=1)
#         date_range = [start_date + timedelta(days=i) for i in range(1)]
#     elif view_type == 'week':
#         # Start from Monday
#         start_date = start_date - timedelta(days=start_date.weekday())
#         end_date = start_date + timedelta(days=7)
#         date_range = [start_date + timedelta(days=i) for i in range(7)]
#     else:  # month
#         # Start from first day of month
#         start_date = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#         next_month = start_date.replace(day=28) + timedelta(days=4)
#         end_date = next_month - timedelta(days=next_month.day)
#         date_range = [start_date + timedelta(days=i) for i in range(31)]  # Max 31 days
    
#     # Get events for the date range
#     events = CalendarEvent.objects.filter(
#         user=request.user,
#         start_time__gte=start_date,
#         start_time__lt=end_date
#     ).order_by('start_time')
    
#     # Get today's events for sidebar
#     todays_events = calendar_manager.get_todays_events()
    
#     # Get unscheduled tasks
#     unscheduled_tasks = Task.objects.filter(
#         assigned_to=request.user,
#         status__in=['todo', 'in_progress'],
#         calendar_events__isnull=True
#     )[:10]
    
#     # Check Google Calendar sync status
#     google_sync = CalendarSync.objects.filter(user=request.user, provider='google', is_active=True).first()
    
#     context = {
#         'events': events,
#         'todays_events': todays_events,
#         'unscheduled_tasks': unscheduled_tasks,
#         'date_range': date_range,
#         'start_date': start_date,
#         'view_type': view_type,
#         'google_sync': google_sync,
#         'now': timezone.now(),
#     }
    
#     return render(request, 'calendar_integration/calendar_view.html', context)

@login_required
def google_calendar_sync(request):
    """Initiate Google Calendar sync"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'connect':
            google_service = GoogleCalendarService(request.user)
            auth_url, state = google_service.get_authorization_url()
            request.session['google_oauth_state'] = state
            return redirect(auth_url)
        
        elif action == 'disconnect':
            CalendarSync.objects.filter(user=request.user, provider='google').update(is_active=False)
            messages.success(request, 'Google Calendar disconnected successfully.')
        
        elif action == 'sync':
            google_service = GoogleCalendarService(request.user)
            synced_count = google_service.sync_calendar_events()
            if synced_count is not False:
                messages.success(request, f'Synced {synced_count} events from Google Calendar.')
            else:
                messages.error(request, 'Failed to sync with Google Calendar.')
    
    return redirect('calendar:calendar_view')

@login_required
def oauth2callback(request):
    """OAuth2 callback for Google Calendar"""
    state = request.session.get('google_oauth_state')
    code = request.GET.get('code')
    
    if state and code:
        google_service = GoogleCalendarService(request.user)
        success = google_service.exchange_code_for_token(code)
        
        if success:
            messages.success(request, 'Google Calendar connected successfully!')
            # Perform initial sync
            google_service.sync_calendar_events()
        else:
            messages.error(request, 'Failed to connect Google Calendar.')
    
    return redirect('calendar:calendar_view')

@login_required
def sync_settings(request):
    """Calendar sync settings"""
    calendar_syncs = CalendarSync.objects.filter(user=request.user)
    working_hours = WorkingHours.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Update working hours
        for day in range(7):
            start_time = request.POST.get(f'start_time_{day}')
            end_time = request.POST.get(f'end_time_{day}')
            is_working = request.POST.get(f'is_working_{day}') == 'on'
            
            if start_time and end_time:
                working_hour, created = WorkingHours.objects.get_or_create(
                    user=request.user,
                    day_of_week=day,
                    defaults={
                        'start_time': start_time,
                        'end_time': end_time,
                        'is_working_day': is_working
                    }
                )
                if not created:
                    working_hour.start_time = start_time
                    working_hour.end_time = end_time
                    working_hour.is_working_day = is_working
                    working_hour.save()
        
        messages.success(request, 'Calendar settings updated successfully!')
        return redirect('calendar:sync_settings')
    
    # Ensure working hours exist for all days
    for day in range(7):
        WorkingHours.objects.get_or_create(
            user=request.user,
            day_of_week=day,
            defaults={
                'start_time': '09:00',
                'end_time': '17:00',
                'is_working_day': day < 5  # Mon-Fri working by default
            }
        )
    
    working_hours = WorkingHours.objects.filter(user=request.user)
    
    return render(request, 'calendar_integration/sync_settings.html', {
        'calendar_syncs': calendar_syncs,
        'working_hours': working_hours,
    })

@login_required
def calendar_events(request):
    """API endpoint for calendar events (for fullcalendar)"""
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    
    if start_str and end_str:
        start = timezone.make_aware(datetime.fromisoformat(start_str.replace('Z', '+00:00')))
        end = timezone.make_aware(datetime.fromisoformat(end_str.replace('Z', '+00:00')))
        
        events = CalendarEvent.objects.filter(
            user=request.user,
            start_time__gte=start,
            end_time__lte=end
        )
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'start': event.start_time.isoformat(),
                'end': event.end_time.isoformat(),
                'color': event.color,
                'extendedProps': {
                    'event_type': event.event_type,
                    'description': event.description,
                    'task_id': event.task.id if event.task else None,
                }
            })
        
        return JsonResponse(events_data, safe=False)
    
    return JsonResponse([], safe=False)

@login_required
def create_calendar_event(request):
    """Create a new calendar event"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        event_type = request.POST.get('event_type', 'task')
        task_id = request.POST.get('task_id')
        color = request.POST.get('color', '#3788d8')
        
        if title and start_time and end_time:
            try:
                start_dt = timezone.make_aware(datetime.fromisoformat(start_time))
                end_dt = timezone.make_aware(datetime.fromisoformat(end_time))
                
                task = None
                if task_id:
                    task = Task.objects.get(id=task_id, assigned_to=request.user)
                
                event = CalendarEvent.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    start_time=start_dt,
                    end_time=end_dt,
                    event_type=event_type,
                    task=task,
                    color=color
                )
                
                # Sync to Google Calendar if connected
                google_sync = CalendarSync.objects.filter(user=request.user, provider='google', is_active=True).first()
                if google_sync:
                    google_service = GoogleCalendarService(request.user)
                    event_data = {
                        'summary': title,
                        'description': description,
                        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'UTC'},
                        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'UTC'},
                        'colorId': google_service._get_google_color_id(color),
                        # 'colorId': self._get_google_color_id(color),
                    }
                    google_event = google_service.create_event(event_data)
                    if google_event:
                        event.external_event_id = google_event['id']
                        event.is_synced = True
                        event.save()
                
                messages.success(request, 'Event created successfully!')
                return redirect('calendar:calendar_view')
                
            except Exception as e:
                messages.error(request, f'Error creating event: {str(e)}')
    
    # Get tasks for dropdown
    tasks = Task.objects.filter(assigned_to=request.user, status__in=['todo', 'in_progress'])
    
    return render(request, 'calendar_integration/create_event.html', {
        'tasks': tasks,
    })

@login_required
def schedule_task(request, task_id):
    """Automatically schedule a task"""
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    calendar_manager = CalendarManager(request.user)
    scheduled_event = calendar_manager.schedule_task(task)
    
    if scheduled_event:
        messages.success(request, f'Task "{task.title}" scheduled successfully!')
    else:
        messages.warning(request, f'No available time slots found for task "{task.title}"')
    
    return redirect('calendar:calendar_view')

@login_required
def create_time_block(request):
    """Create a time block for focused work"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        block_type = request.POST.get('block_type', 'focus')
        task_ids = request.POST.getlist('tasks')
        is_recurring = request.POST.get('is_recurring') == 'on'
        recurrence_days = request.POST.get('recurrence_days', '')
        
        if title and start_time and end_time:
            try:
                start_dt = timezone.make_aware(datetime.fromisoformat(start_time))
                end_dt = timezone.make_aware(datetime.fromisoformat(end_time))
                
                time_block = TimeBlock.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    start_time=start_dt,
                    end_time=end_dt,
                    block_type=block_type,
                    is_recurring=is_recurring,
                    recurrence_days=recurrence_days
                )
                
                if task_ids:
                    tasks = Task.objects.filter(id__in=task_ids, assigned_to=request.user)
                    time_block.tasks.set(tasks)
                
                # Also create a calendar event
                CalendarEvent.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    start_time=start_dt,
                    end_time=end_dt,
                    event_type='focus_block',
                    color='#8b5cf6'  # Purple for focus time
                )
                
                messages.success(request, 'Time block created successfully!')
                return redirect('calendar:calendar_view')
                
            except Exception as e:
                messages.error(request, f'Error creating time block: {str(e)}')
    
    tasks = Task.objects.filter(assigned_to=request.user, status__in=['todo', 'in_progress'])
    return render(request, 'calendar_integration/create_time_block.html', {'tasks': tasks})

@login_required
def get_available_slots(request):
    """API endpoint to get available time slots"""
    duration = float(request.GET.get('duration', 1))
    days = int(request.GET.get('days', 7))
    
    calendar_manager = CalendarManager(request.user)
    slots = calendar_manager.find_available_slots(duration, days)
    
    slots_data = []
    for slot in slots:
        slots_data.append({
            'start': slot['start'].isoformat(),
            'end': slot['end'].isoformat(),
            'duration': slot['duration']
        })
    
    return JsonResponse({'slots': slots_data})

def _get_google_color_id(self, hex_color):
    """Map hex colors to Google Calendar color IDs"""
    color_map = {
        '#3788d8': '1',  # Blue
        '#dc2626': '2',  # Red
        '#16a34a': '3',  # Green
        '#9333ea': '4',  # Purple
        '#ea580c': '5',  # Orange
        '#0891b2': '6',  # Teal
        '#dc267f': '7',  # Pink
        '#ffb000': '8',  # Yellow
        '#8b5cf6': '9',  # Violet
        '#10b981': '10', # Emerald
    }
    return color_map.get(hex_color, '1')

#OLD CODE - DO NOT USE
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required

# # Create your views here.

# @login_required
# def calendar_view(request):
#     return render(request, 'calendar_integration/calendar_view.html')

# @login_required
# def google_calendar_sync(request):
#     return render(request, 'calendar_integration/sync_google.html')

# @login_required
# def oauth2callback(request):
#     return render(request, 'calendar_integration/oauth_callback.html')

# @login_required
# def sync_settings(request):
#     return render(request, 'calendar_integration/sync_settings.html')

# @login_required
# def calendar_events(request):
#     return render(request, 'calendar_integration/events.html')

# @login_required
# def create_calendar_event(request):
#     return render(request, 'calendar_integration/create_event.html')