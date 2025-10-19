# Create your models here.
from django.db import models
from django.conf import settings

class CalendarSync(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # 'google', 'outlook', etc.
    is_active = models.BooleanField(default=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.provider}"