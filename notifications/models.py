# notifications/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import uuid

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_due', 'Task Due Soon'),
        ('task_overdue', 'Task Overdue'),
        ('task_comment', 'Task Comment'),
        ('team_invite', 'Team Invitation'),
        ('team_message', 'Team Message'),
        ('file_shared', 'File Shared'),
        ('mention', 'Mention'),
        ('project_update', 'Project Update'),
        ('system', 'System Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related object references
    related_object_id = models.UUIDField(null=True, blank=True)
    related_content_type = models.CharField(max_length=100, blank=True)
    
    # Additional data for the notification
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    def get_absolute_url(self):
        """Get URL to the related object if possible"""
        if self.related_object_id and self.related_content_type:
            if self.related_content_type == 'task':
                return reverse('tasks:task_detail', kwargs={'pk': self.related_object_id})
            elif self.related_content_type == 'team':
                return reverse('users:team_detail', kwargs={'team_id': self.related_object_id})
            elif self.related_content_type == 'project':
                return reverse('tasks:project_detail', kwargs={'pk': self.related_object_id})
        return '#'
    
    @property
    def is_recent(self):
        """Check if notification was created in the last 5 minutes"""
        return (timezone.now() - self.created_at).total_seconds() < 300
