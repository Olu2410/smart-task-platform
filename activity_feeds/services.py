from django.contrib.contenttypes.models import ContentType
from .models import Activity

class ActivityService:
    @staticmethod
    def record_activity(team, user, activity_type, description, content_object=None, metadata=None):
        """Record an activity in the feed"""
        return Activity.create_activity(
            team=team,
            user=user,
            activity_type=activity_type,
            description=description,
            content_object=content_object,
            metadata=metadata or {}
        )
    
    @staticmethod
    def task_created(task, user):
        """Record task creation activity"""
        return ActivityService.record_activity(
            team=task.project.team,
            user=user,
            activity_type='task_created',
            description=f'{user.get_full_name()} created task "{task.title}"',
            content_object=task,
            metadata={
                'task_title': task.title,
                'project_name': task.project.name,
            }
        )
    
    @staticmethod
    def task_completed(task, user):
        """Record task completion activity"""
        return ActivityService.record_activity(
            team=task.project.team,
            user=user,
            activity_type='task_completed',
            description=f'{user.get_full_name()} completed task "{task.title}"',
            content_object=task,
            metadata={
                'task_title': task.title,
                'project_name': task.project.name,
            }
        )
    
    @staticmethod
    def message_sent(channel, message):
        """Record message activity"""
        return ActivityService.record_activity(
            team=channel.team,
            user=message.user,
            activity_type='message_sent',
            description=f'{message.user.get_full_name()} sent a message in #{channel.name}',
            content_object=message,
            metadata={
                'channel_name': channel.name,
                'message_preview': message.content[:100],
            }
        )
    
    @staticmethod
    def file_uploaded(file_share):
        """Record file upload activity"""
        return ActivityService.record_activity(
            team=file_share.team,
            user=file_share.uploaded_by,
            activity_type='file_uploaded',
            description=f'{file_share.uploaded_by.get_full_name()} uploaded "{file_share.filename}"',
            content_object=file_share,
            metadata={
                'filename': file_share.filename,
                'file_type': file_share.file_type,
                'file_size': file_share.file_size,
            }
        )

class ActivityQueryService:
    @staticmethod
    def get_team_activities(team, days=7, limit=50):
        """Get recent activities for a team"""
        from django.utils import timezone
        from datetime import timedelta
        
        since_date = timezone.now() - timedelta(days=days)
        
        return Activity.objects.filter(
            team=team,
            created_at__gte=since_date
        ).select_related('user').order_by('-created_at')[:limit]
    
    @staticmethod
    def get_user_activities(user, teams=None, limit=30):
        """Get activities for user (across their teams)"""
        queryset = Activity.objects.filter(team__members=user)
        
        if teams:
            queryset = queryset.filter(team__in=teams)
        
        return queryset.select_related('user', 'team').order_by('-created_at')[:limit]