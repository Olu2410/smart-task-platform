from django.urls import path
from . import views

app_name = 'activity_feeds'

urlpatterns = [
    path('', views.user_activity_feed, name='user_activity_feed'),
    path('team/<int:team_id>/', views.team_activity_feed, name='team_activity_feed'),
    path('api/activities/', views.activity_feed_api, name='activity_feed_api'),
    path('api/activities/team/<int:team_id>/', views.activity_feed_api, name='team_activity_feed_api'),
]