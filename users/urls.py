from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/availability/', views.profile_availability, name='profile_availability'),
    
    # Teams
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/invite/', views.team_invite, name='team_invite'),
    
    # Invitations
    path('invitations/', views.invitations_list, name='invitations_list'),
    path('invitations/<str:token>/<str:action>/', views.invitation_respond, name='invitation_respond'),
]