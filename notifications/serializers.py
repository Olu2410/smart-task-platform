#notifications/serializers.py
from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    is_recent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 
            'is_read', 'created_at', 'url', 'is_recent', 'metadata'
        ]
        read_only_fields = fields
    
    def get_url(self, obj):
        return obj.get_absolute_url()