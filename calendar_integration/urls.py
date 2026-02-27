from django.urls import path
from . import views

app_name = 'calendar'

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('events/', views.calendar_events, name='calendar_events'),
    path('events/create/', views.create_calendar_event, name='create_calendar_event'),
    path('time-blocks/create/', views.create_time_block, name='create_time_block'),
    path('schedule-task/<int:task_id>/', views.schedule_task, name='schedule_task'),
    path('available-slots/', views.get_available_slots, name='get_available_slots'),
    
    # Google Calendar integration
    path('google/sync/', views.google_calendar_sync, name='google_calendar_sync'),
    path('google/oauth2callback/', views.oauth2callback, name='oauth2callback'),
    
    # Settings
    path('settings/', views.sync_settings, name='sync_settings'),
]

