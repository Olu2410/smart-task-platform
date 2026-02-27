
# Create your models here.
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('task_created', 'Task Created'),
        ('task_updated', 'Task Updated'),
        ('task_completed', 'Task Completed'),
        ('task_assigned', 'Task Assigned'),
        ('comment_added', 'Comment Added'),
        ('file_uploaded', 'File Uploaded'),
        ('project_created', 'Project Created'),
        ('team_joined', 'Team Joined'),
        ('message_sent', 'Message Sent'),
        ('meeting_scheduled', 'Meeting Scheduled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey('users.Team', on_delete=models.CASCADE, related_name='activities')
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Generic foreign key to any related object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['team', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.team.name}"
    
    @property
    def is_recent(self):
        """Check if activity was created in the last hour"""
        return (timezone.now() - self.created_at).total_seconds() < 3600
    
    @classmethod
    def create_activity(cls, team, user, activity_type, description, content_object=None, metadata=None):
        """Helper method to create activity with proper content type"""
        activity = cls(
            team=team,
            user=user,
            activity_type=activity_type,
            description=description,
            metadata=metadata or {}
        )
        
        if content_object:
            activity.content_type = ContentType.objects.get_for_model(content_object)
            activity.object_id = content_object.pk
        
        activity.save()
        return activity