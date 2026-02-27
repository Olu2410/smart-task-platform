# team_chat/urls.py
from django.urls import path
from . import views

app_name = 'team_chat'

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    # Team uses integer ID
    path('team/<int:team_id>/channels/', views.channel_list, name='channel_list'),
    path('team/<int:team_id>/create-channel/', views.create_channel, name='create_channel'),
    # Channel uses UUID
    path('channel/<uuid:channel_id>/', views.channel_detail, name='channel_detail'),
    path('channel/<uuid:channel_id>/send/', views.send_message, name='send_message'),
    path('channel/<uuid:channel_id>/upload/', views.upload_file, name='upload_file'),
    path('file/<uuid:file_id>/download/', views.download_file, name='download_file'),
]

# urlpatterns = [
#     path('', views.chat_home, name='chat_home'),
#     path('team/<uuid:team_id>/channels/', views.channel_list, name='channel_list'),
#     path('channel/<uuid:channel_id>/', views.channel_detail, name='channel_detail'),
#     path('channel/<uuid:channel_id>/send/', views.send_message, name='send_message'),
#     path('channel/<uuid:channel_id>/upload/', views.upload_file, name='upload_file'),
#     path('file/<uuid:file_id>/download/', views.download_file, name='download_file'),
#     path('team/<uuid:team_id>/create-channel/', views.create_channel, name='create_channel'),
# ]