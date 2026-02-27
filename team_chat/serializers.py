# team_chat/serializers.py
from rest_framework import serializers
from .models import TeamChannel, ChannelMessage, FileShare

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField(source='get_full_name')

class TeamChannelSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(source='messages.count', read_only=True)
    
    class Meta:
        model = TeamChannel
        fields = ['id', 'team', 'name', 'description', 'is_private', 'created_by', 'created_at', 'message_count']
        read_only_fields = ['id', 'created_by', 'created_at']

class ChannelMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ChannelMessage
        fields = [
            'id', 'channel', 'user', 'message_type', 'content',
            'file_attachment', 'parent_message', 'reactions',
            'reply_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class CreateChannelMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelMessage
        fields = ['channel', 'content', 'parent_message']

class FileShareSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    download_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = FileShare
        fields = [
            'id', 'team', 'uploaded_by', 'file', 'filename',
            'file_type', 'file_size', 'file_size_mb', 'description',
            'is_public', 'allowed_users', 'created_at', 'download_url'
        ]
        read_only_fields = ['id', 'uploaded_by', 'filename', 'file_size', 'created_at']