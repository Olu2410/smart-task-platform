# team_chat/models.py
# Create your models here. 
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class TeamChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey('users.Team', on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    created_by = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['team', 'name']
    
    def __str__(self):
        return f"{self.team.name} - {self.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('team_chat:channel_detail', kwargs={'channel_id': self.id})

class ChannelMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text Message'),
        ('file', 'File Upload'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(TeamChannel, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    
    # For file messages
    file_attachment = models.ForeignKey('team_chat.FileShare', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Message threading
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Reactions (stored as JSON)
    reactions = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['channel', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.channel.name}: {self.content[:50]}"
    
    @property
    def reply_count(self):
        return self.replies.count()
    
    def add_reaction(self, user, emoji):
        """Add a reaction to the message"""
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        
        if user.id not in self.reactions[emoji]:
            self.reactions[emoji].append(user.id)
            self.save()
    
    def remove_reaction(self, user, emoji):
        """Remove a reaction from the message"""
        if emoji in self.reactions and user.id in self.reactions[emoji]:
            self.reactions[emoji].remove(user.id)
            if not self.reactions[emoji]:
                del self.reactions[emoji]
            self.save()

class FileShare(models.Model):
    FILE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archive'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey('users.Team', on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    file = models.FileField(upload_to='team_files/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.BigIntegerField()  # Size in bytes
    description = models.TextField(blank=True)
    
    # Sharing settings
    is_public = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField('users.CustomUser', blank=True, related_name='accessible_files')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.team.name}"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def download_url(self):
        return self.file.url
    
    def can_access(self, user):
        """Check if user can access this file"""
        if self.is_public:
            return True
        if user == self.uploaded_by:
            return True
        if self.team.members.filter(id=user.id).exists():
            return True
        return self.allowed_users.filter(id=user.id).exists()