# Create your views here.
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import uuid

from tasks.models import Project
from .models import CustomUser, Team, TeamMembership, Invitation, UserAvailability
from .forms import (CustomUserCreationForm, LoginForm, ProfileUpdateForm,
                   TeamCreationForm, TeamUpdateForm, InvitationForm, AvailabilityForm)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Auto-login after registration
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Smart Task Platform.')
            
            # Check for pending invitations
            pending_invitations = Invitation.objects.filter(
                email=user.email, 
                status='pending',
                expires_at__gt=timezone.now()
            )
            
            if pending_invitations.exists():
                messages.info(request, f'You have {pending_invitations.count()} pending team invitation(s).')
                return redirect('users:invitations_list')
            
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('users:login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # Handle avatar deletion
            if 'avatar-clear' in request.POST and request.user.avatar:
                # Delete the old avatar file
                if os.path.isfile(request.user.avatar.path):
                    os.remove(request.user.avatar.path)
                request.user.avatar = None
            
            user = form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    # Get user's teams
    user_teams = Team.objects.filter(members=request.user)
    user_memberships = TeamMembership.objects.filter(user=request.user).select_related('team')
    
    # Get user availability
    availability_schedule = UserAvailability.objects.filter(user=request.user)
    
    return render(request, 'users/profile.html', {
        'form': form,
        'user_teams': user_teams,
        'user_memberships': user_memberships,
        'availability_schedule': availability_schedule,
    })

# @login_required
# def profile_view(request):
#     if request.method == 'POST':
#         form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Profile updated successfully!')
#             return redirect('users:profile')
#     else:
#         form = ProfileUpdateForm(instance=request.user)
    
#     # Get user's teams
#     user_teams = Team.objects.filter(members=request.user)
#     user_memberships = TeamMembership.objects.filter(user=request.user).select_related('team')
    
#     return render(request, 'users/profile.html', {
#         'form': form,
#         'user_teams': user_teams,
#         'user_memberships': user_memberships,
#     })



@login_required
def profile_availability(request):
    """Manage user availability schedule"""
    availabilities = UserAvailability.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Handle bulk availability updates
        if 'bulk_update' in request.POST:
            days_data = request.POST.get('days', '').split(',')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            for day_str in days_data:
                if day_str.strip():
                    day = int(day_str)
                    availability, created = UserAvailability.objects.get_or_create(
                        user=request.user,
                        day_of_week=day,
                        defaults={
                            'start_time': start_time,
                            'end_time': end_time,
                            'is_working_day': True
                        }
                    )
                    if not created:
                        availability.start_time = start_time
                        availability.end_time = end_time
                        availability.is_working_day = True
                        availability.save()
            
            messages.success(request, 'Availability schedule updated!')
            return redirect('users:profile_availability')
        
        # Handle single day update
        else:
            form = AvailabilityForm(request.POST)
            if form.is_valid():
                availability = form.save(commit=False)
                availability.user = request.user
                
                # Check for existing availability for this day
                existing = UserAvailability.objects.filter(
                    user=request.user,
                    day_of_week=availability.day_of_week
                ).first()
                
                if existing:
                    existing.start_time = availability.start_time
                    existing.end_time = availability.end_time
                    existing.is_working_day = availability.is_working_day
                    existing.save()
                    messages.success(request, f'Availability for {existing.get_day_of_week_display()} updated!')
                else:
                    availability.save()
                    messages.success(request, f'Availability for {availability.get_day_of_week_display()} added!')
                
                return redirect('users:profile_availability')
    else:
        form = AvailabilityForm()
    
    days_of_week = dict(UserAvailability._meta.get_field('day_of_week').choices)
    
    # Get default work hours from user profile
    default_start = request.user.workday_start.strftime('%H:%M') if request.user.workday_start else '09:00'
    default_end = request.user.workday_end.strftime('%H:%M') if request.user.workday_end else '17:00'
    
    return render(request, 'users/availability.html', {
        'availabilities': availabilities,
        'form': form,
        'days_of_week': days_of_week,
        'default_start': default_start,
        'default_end': default_end,
    })

# @login_required
# def profile_availability(request):
#     availabilities = UserAvailability.objects.filter(user=request.user)
    
#     if request.method == 'POST':
#         form = AvailabilityForm(request.POST)
#         if form.is_valid():
#             availability = form.save(commit=False)
#             availability.user = request.user
            
#             # Check for existing availability for this day
#             existing = UserAvailability.objects.filter(
#                 user=request.user,
#                 day_of_week=availability.day_of_week
#             ).first()
            
#             if existing:
#                 existing.start_time = availability.start_time
#                 existing.end_time = availability.end_time
#                 existing.is_working_day = availability.is_working_day
#                 existing.save()
#                 messages.success(request, f'Availability for {existing.get_day_of_week_display()} updated!')
#             else:
#                 availability.save()
#                 messages.success(request, f'Availability for {availability.get_day_of_week_display()} added!')
            
#             return redirect('profile_availability')
#     else:
#         form = AvailabilityForm()
    
#     days_of_week = dict(UserAvailability._meta.get_field('day_of_week').choices)
    
#     return render(request, 'users/availability.html', {
#         'availabilities': availabilities,
#         'form': form,
#         'days_of_week': days_of_week,
#     })


@login_required
def delete_availability(request, availability_id):
    """Delete a specific availability entry"""
    availability = get_object_or_404(UserAvailability, id=availability_id, user=request.user)
    
    if request.method == 'POST':
        day_name = availability.get_day_of_week_display()
        availability.delete()
        messages.success(request, f'Availability for {day_name} removed!')
    
    return redirect('users:profile_availability')

@login_required
def set_default_availability(request):
    """Set default availability based on user's work hours"""
    if request.method == 'POST':
        # Delete existing availabilities
        UserAvailability.objects.filter(user=request.user).delete()
        
        # Create new availabilities for work days
        work_days = request.user.get_working_days_list()
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name in work_days:
            day_number = day_mapping.get(day_name.lower())
            if day_number is not None:
                UserAvailability.objects.create(
                    user=request.user,
                    day_of_week=day_number,
                    start_time=request.user.workday_start,
                    end_time=request.user.workday_end,
                    is_working_day=True
                )
        
        messages.success(request, 'Default availability schedule set based on your work hours!')
    
    return redirect('users:profile_availability')


@login_required
def team_list(request):
    """List all teams the user belongs to"""
    user_teams = Team.objects.filter(members=request.user)
    public_teams = Team.objects.filter(is_public=True).exclude(members=request.user)
    # teams = Team.objects.filter(members=request.user).annotate(
    #     member_count=Count('members'),
    #     project_count=Count('project', distinct=True),
    #     channel_count=Count('channels', distinct=True)  # Add this if you have the channels relation
    # )
    return render(request, 'users/team_list.html', {
        'teams': user_teams,
        'public_teams': public_teams,
    })

@login_required
def team_create(request):
    if request.method == 'POST':
        form = TeamCreationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            
            # Add creator as admin
            TeamMembership.objects.create(
                user=request.user,
                team=team,
                role='admin'
            )
            
            messages.success(request, f'Team "{team.name}" created successfully!')
            return redirect('users:team_detail', team_id=team.id)
    else:
        form = TeamCreationForm()
    
    return render(request, 'users/team_create.html', {'form': form})

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    membership = get_object_or_404(TeamMembership, team=team, user=request.user)
    
    # Get team members with their roles
    members = TeamMembership.objects.filter(team=team).select_related('user')
    
    # Get pending invitations
    pending_invitations = Invitation.objects.filter(team=team, status='pending')
    
    return render(request, 'users/team_detail.html', {
        'team': team,
        'membership': membership,
        'members': members,
        'pending_invitations': pending_invitations,
    })

@login_required
def team_invite(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    membership = get_object_or_404(TeamMembership, team=team, user=request.user)
    
    # Check if user has permission to invite
    if membership.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to invite members to this team.')
        return redirect('team_detail', team_id=team_id)
    
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            emails = form.cleaned_data['emails']
            role = form.cleaned_data['role']
            
            invited_count = 0
            for email in emails:
                # Check if user is already a member
                if team.members.filter(email=email).exists():
                    messages.warning(request, f'{email} is already a team member.')
                    continue
                
                # Check for existing pending invitation
                existing_invite = Invitation.objects.filter(
                    email=email,
                    team=team,
                    status='pending'
                ).first()
                
                if existing_invite:
                    messages.warning(request, f'Pending invitation already exists for {email}.')
                    continue
                
                # Create new invitation
                invitation = Invitation.objects.create(
                    email=email,
                    team=team,
                    invited_by=request.user,
                    token=str(uuid.uuid4()),
                    role=role,
                    expires_at=timezone.now() + timezone.timedelta(days=7)
                )
                
                # Send invitation email
                send_invitation_email(invitation, request)
                
                invited_count += 1
            
            if invited_count > 0:
                messages.success(request, f'Invitations sent to {invited_count} email(s).')
            else:
                messages.warning(request, 'No invitations were sent.')
            
            return redirect('users:team_detail', team_id=team_id)
    else:
        form = InvitationForm()

    pending_invitations = Invitation.objects.filter(
        team=team,
        status='pending',
        expires_at__gt=timezone.now()
    )
    
    return render(request, 'users/team_invite.html', {
        'team': team,
        'form': form,
        'pending_invitations': pending_invitations,
    })

@login_required
def invitations_list(request):
    pending_invitations = Invitation.objects.filter(
        email=request.user.email,
        status='pending',
        expires_at__gt=timezone.now()
    ).select_related('team', 'invited_by')
    
    return render(request, 'users/invitations_list.html', {
        'pending_invitations': pending_invitations,
    })


def send_invitation_email(invitation, request):
    subject = f'Invitation to join team "{invitation.team.name}"'
    
    # Build absolute URL for invitation acceptance
    accept_url = request.build_absolute_uri(
        f'/users/invitations/{invitation.token}/accept/'
    )
    
    context = {
        'team': invitation.team,
        'invited_by': invitation.invited_by,
        'accept_url': accept_url,
        'expires_at': invitation.expires_at,
    }
    
    message = render_to_string('users/email/invitation.txt', context)
    html_message = render_to_string('users/email/invitation.html', context)
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [invitation.email],
        html_message=html_message,
        fail_silently=False,
    )


@login_required
def invitation_cancel(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)

    # Only admins or managers of that team may cancel
    membership = TeamMembership.objects.filter(
        team=invitation.team,
        user=request.user
    ).first()

    if not membership or membership.role not in ['admin', 'manager']:
        messages.error(request, "You do not have permission to cancel this invitation.")
        return redirect('users:team_detail', team_id=invitation.team.id)

    if invitation.status != 'pending':
        messages.warning(request, "This invitation is no longer active.")
        return redirect('users:team_invite', team_id=invitation.team.id)

    # Cancel it
    invitation.status = 'expired'
    invitation.save()

    messages.success(request, f"Invitation to {invitation.email} has been cancelled.")
    return redirect('users:team_invite', team_id=invitation.team.id)


@login_required
def invitation_respond(request, token, action):
    invitation = get_object_or_404(Invitation, token=token, email=request.user.email)
    
    if invitation.status != 'pending' or invitation.is_expired():
        messages.error(request, 'This invitation is no longer valid.')
        return redirect('dashboard')
    
    if action == 'accept':
        # Add user to team
        TeamMembership.objects.create(
            user=request.user,
            team=invitation.team,
            role=invitation.role
        )
        
        invitation.status = 'accepted'
        invitation.save()
        
        messages.success(request, f'You have joined the team "{invitation.team.name}"!')
        
    elif action == 'decline':
        invitation.status = 'declined'
        invitation.save()
        messages.info(request, f'You have declined the invitation to join "{invitation.team.name}".')
    
    return redirect('dashboard')