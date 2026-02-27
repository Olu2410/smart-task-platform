#notifications/services.py
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import Notification
from .serializers import NotificationSerializer


class NotificationService:
    @staticmethod
    def _get_user_model():
        """Helper to safely get the user model."""
        from django.contrib.auth import get_user_model
        return get_user_model()
    
    @staticmethod
    def create_notification(user, notification_type, title, message, related_object=None, metadata=None):
        """Create a notification and send via WebSocket"""
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                metadata=metadata or {},
            )
            
            if related_object:
                from django.contrib.contenttypes.models import ContentType
                notification.related_object_id = related_object.pk
                notification.related_content_type = ContentType.objects.get_for_model(related_object).model
                notification.save()
        
        # Send via WebSocket
        NotificationService.send_websocket_notification(user, notification)
        
        return notification
    
    @staticmethod
    def send_websocket_notification(user, notification):
        """Send notification via WebSocket"""
        channel_layer = get_channel_layer()

        notification_data = NotificationSerializer(notification).data
        # notification_data = {
        #     'id': str(notification.id),
        #     'type': notification.notification_type,
        #     'title': notification.title,
        #     'message': notification.message,
        #     'created_at': notification.created_at.isoformat(),
        #     'is_read': notification.is_read,
        #     'url': notification.get_absolute_url(),
        # }
        
        async_to_sync(channel_layer.group_send)(
            f'user_{user.id}_notifications',
            {
                'type': 'send_notification',
                'notification': notification_data
            }
        )
    
    @staticmethod
    def notify_task_assigned(task, assigned_by):
        """Notify user about task assignment"""
        if task.assigned_to and task.assigned_to != assigned_by:
            NotificationService.create_notification(
                user=task.assigned_to,
                notification_type='task_assigned',
                title=f'New Task Assigned',
                message=f'{assigned_by.get_full_name()} assigned you the task "{task.title}"',
                related_object=task,
                metadata={
                    'task_title': task.title,
                    'project_name': task.project.name,
                    'assigned_by': assigned_by.get_full_name(),
                }
            )
    
    @staticmethod
    def notify_task_due(task):
        """Notify user about due task"""
        if task.assigned_to and task.due_date:
            NotificationService.create_notification(
                user=task.assigned_to,
                notification_type='task_due',
                title=f'Task Due Soon',
                message=f'Task "{task.title}" is due on {task.due_date.strftime("%b %d")}',
                related_object=task,
                metadata={
                    'task_title': task.title,
                    'due_date': task.due_date.isoformat(),
                }
            )
    
    @staticmethod
    def notify_team_message(channel, message, mentioned_users=None):
        """Notify team members about new message"""
        mentioned_users = mentioned_users or []
        
        for member in channel.team.members.exclude(id=message.user.id):
            notification_type = 'team_message'
            title = f'New message in {channel.name}'
            message_text = f'{message.user.get_full_name()}: {message.content[:100]}...'
            
            # Check if user was mentioned
            if member in mentioned_users:
                notification_type = 'mention'
                title = f'You were mentioned in {channel.name}'
            
            NotificationService.create_notification(
                user=member,
                notification_type=notification_type,
                title=title,
                message=message_text,
                related_object=channel,
                metadata={
                    'channel_name': channel.name,
                    'team_name': channel.team.name,
                    'message_preview': message.content[:200],
                    'mentioned': member in mentioned_users,
                }
            )
    
    @staticmethod
    def notify_file_shared(file_share, shared_with_users=None):
        """Notify users about shared file"""
        shared_with_users = shared_with_users or []
        
        for user in shared_with_users:
            NotificationService.create_notification(
                user=user,
                notification_type='file_shared',
                title=f'File Shared with You',
                message=f'{file_share.uploaded_by.get_full_name()} shared "{file_share.filename}"',
                related_object=file_share,
                metadata={
                    'filename': file_share.filename,
                    'file_type': file_share.file_type,
                    'file_size': file_share.file_size,
                    'shared_by': file_share.uploaded_by.get_full_name(),
                }
            )

class BulkNotificationService:
    @staticmethod
    def notify_team(team, notification_type, title, message, exclude_user=None, related_object=None):
        """Send notification to all team members"""
        users = team.members.all()
        if exclude_user:
            users = users.exclude(id=exclude_user.id)
        
        for user in users:
            NotificationService.create_notification(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
                related_object=related_object,
            )