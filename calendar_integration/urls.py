from django.urls import path
from . import views

app_name = 'calendar_integration'
# app_name = 'calendar'

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('sync/google/', views.google_calendar_sync, name='google_calendar_sync'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('sync/settings/', views.sync_settings, name='sync_settings'),
    path('events/', views.calendar_events, name='calendar_events'),
    path('events/create/', views.create_calendar_event, name='create_calendar_event'),
]
