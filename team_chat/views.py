# team_chat/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
import os
from .models import TeamChannel, ChannelMessage, FileShare
from .forms import ChannelMessageForm, FileShareForm
from notifications.services import NotificationService
from activity_feeds.services import ActivityService

@login_required
def chat_home(request):
    """Main chat homepage - shows teams with chat access"""
    from users.models import Team
    
    user_teams = Team.objects.filter(members=request.user).prefetch_related('channels')
    
    # If user has only one team, redirect to that team's channels
    if user_teams.count() == 1:
        team = user_teams.first()
        return redirect('team_chat:channel_list', team_id=team.id)
    
    # If user has teams but no channels in any team, suggest creating one
    has_channels = any(team.channels.exists() for team in user_teams)
    
    return render(request, 'team_chat/chat_home.html', {
        'user_teams': user_teams,
        'has_channels': has_channels,
        'team_count': user_teams.count(),
    })


@login_required
def channel_list(request, team_id):
    """List channels for a team"""
    from users.models import Team
    team = get_object_or_404(Team, id=team_id, members=request.user)
    channels = team.channels.all()
    
    return render(request, 'team_chat/channel_list.html', {
        'team': team,
        'channels': channels,
    })

@login_required
def channel_detail(request, channel_id):
    """Display channel messages and chat interface"""
    channel = get_object_or_404(TeamChannel, id=channel_id)
    
    # Check if user has access to this channel
    if not channel.team.members.filter(id=request.user.id).exists():
        return redirect('users:team_list')
    
    messages = channel.messages.select_related('user').prefetch_related('replies')[:100]
    message_form = ChannelMessageForm()
    file_form = FileShareForm()
    
    return render(request, 'team_chat/channel_detail.html', {
        'channel': channel,
        'messages': messages,
        'message_form': message_form,
        'file_form': file_form,
    })


@login_required
@require_http_methods(['POST'])
def send_message(request, channel_id):
    """Send a message to a channel"""
    channel = get_object_or_404(TeamChannel, id=channel_id)
    
    if not channel.team.members.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Message content is required'}, status=400)
    
    # Create message
    message = ChannelMessage.objects.create(
        channel=channel,
        user=request.user,
        content=content
    )
    
    # Record activity
    try:
        ActivityService.message_sent(channel, message)
    except:
        pass  # Skip if activity service fails
    
    # Send notifications
    try:
        NotificationService.notify_team_message(channel, message)
    except:
        pass  # Skip if notification service fails
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message_id': str(message.id),
            'message': {
                'id': str(message.id),
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'full_name': request.user.get_full_name() or request.user.username,
                },
                'content': message.content,
                'message_type': message.message_type,
                'created_at': message.created_at.isoformat(),
                'is_file': False,
            }
        })
    
    return redirect('team_chat:channel_detail', channel_id=channel_id)

# @login_required
# @require_http_methods(['POST'])
# def send_message(request, channel_id):
#     """Send a message to a channel"""
#     channel = get_object_or_404(TeamChannel, id=channel_id)
    
#     if not channel.team.members.filter(id=request.user.id).exists():
#         return JsonResponse({'error': 'Access denied'}, status=403)
    
#     form = ChannelMessageForm(request.POST)
#     if form.is_valid():
#         message = form.save(commit=False)
#         message.channel = channel
#         message.user = request.user
#         message.save()
        
#         # Record activity
#         ActivityService.message_sent(channel, message)
        
#         # Send notifications
#         NotificationService.notify_team_message(channel, message)
        
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return JsonResponse({
#                 'success': True,
#                 'message_id': str(message.id),
#             })
    
#     # Handle form errors for AJAX requests
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return JsonResponse({
#             'success': False,
#             'errors': form.errors
#         }, status=400)
    
#     return redirect('team_chat:channel_detail', channel_id=channel_id)

@login_required
@require_http_methods(['POST'])
def upload_file(request, channel_id):
    """Upload and share a file in channel"""
    channel = get_object_or_404(TeamChannel, id=channel_id)
    
    if not channel.team.members.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    form = FileShareForm(request.POST, request.FILES)
    if form.is_valid():
        file_share = form.save(commit=False)
        file_share.team = channel.team
        file_share.uploaded_by = request.user
        file_share.file_size = request.FILES['file'].size
        file_share.filename = request.FILES['file'].name
        
        # Determine file type
        import os
        from django.conf import settings
        ext = os.path.splitext(file_share.filename)[1].lower()
        file_share.file_type = 'other'
        
        for file_type, extensions in settings.ALLOWED_FILE_EXTENSIONS.items():
            if ext in extensions:
                file_share.file_type = file_type
                break
        
        file_share.save()
        
        # Create file message
        message = ChannelMessage.objects.create(
            channel=channel,
            user=request.user,
            message_type='file',
            content=f"Shared file: {file_share.filename}",
            file_attachment=file_share
        )
        
        # Record activity
        ActivityService.file_uploaded(file_share)
        
        # Send notifications
        NotificationService.notify_file_shared(file_share, list(channel.team.members.all()))
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'file_id': str(file_share.id),
                'message_id': str(message.id),
            })
    
    # Handle form errors for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)
    
    return redirect('team_chat:channel_detail', channel_id=channel_id)

@login_required
def download_file(request, file_id):
    """Download a shared file"""
    file_share = get_object_or_404(FileShare, id=file_id)
    
    if not file_share.can_access(request.user):
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    response = FileResponse(file_share.file.open(), as_attachment=True, filename=file_share.filename)
    return response

@login_required
@require_http_methods(['POST'])
def create_channel(request, team_id):
    """Create a new channel in a team"""
    from users.models import Team
    
    # team_id might come as string or int, convert to int
    try:
        team_id = int(team_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid team ID'}, status=400)
    
    team = get_object_or_404(Team, id=team_id, members=request.user)
    
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    is_private = request.POST.get('is_private', 'false') == 'true'
    
    if not name:
        return JsonResponse({'error': 'Channel name is required'}, status=400)
    
    # Create the channel
    channel = TeamChannel.objects.create(
        team=team,
        name=name,
        description=description,
        is_private=is_private,
        created_by=request.user
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'channel_id': str(channel.id),  # This is UUID
            'channel_name': channel.name
        })
    
    return redirect('team_chat:channel_list', team_id=team_id)

# @login_required
# @require_http_methods(['POST'])
# def create_channel(request, team_id):
#     """Create a new channel in a team"""
#     from users.models import Team
#     team = get_object_or_404(Team, id=team_id, members=request.user)
    
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         description = request.POST.get('description', '')
#         is_private = request.POST.get('is_private', False) == 'true'
        
#         if name:
#             channel = TeamChannel.objects.create(
#                 team=team,
#                 name=name,
#                 description=description,
#                 is_private=is_private,
#                 created_by=request.user
#             )
            
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': True,
#                     'channel_id': str(channel.id),
#                     'channel_name': channel.name
#                 })
    
#     return redirect('team_chat:channel_list', team_id=team_id)