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
    path('profile/availability/<int:availability_id>/delete/', views.delete_availability, name='delete_availability'),
    path('profile/availability/set-default/', views.set_default_availability, name='set_default_availability'),

    # path('profile/password/', views.change_password, name='change_password'),

    # Teams
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/invite/', views.team_invite, name='team_invite'),
    
    # Invitations
    path('invitations/', views.invitations_list, name='invitations_list'),
    path('invitations/<int:invitation_id>/cancel/', views.invitation_cancel, name='invitation_cancel'),
    path('invitations/<str:token>/<str:action>/', views.invitation_respond, name='invitation_respond'),

]
