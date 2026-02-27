

from django.urls import path
from . import views

# app_name = 'notifications'

# urlpatterns = [
#     path('', views.notifications_list, name='notifications_list'),
#     path('mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
#     path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
#     path('settings/', views.notification_settings, name='notification_settings'),
# ]

# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('count/', views.notification_count, name='notification_count'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('<uuid:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
]
