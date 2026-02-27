from rest_framework import serializers
from .models import Activity

class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField(source='get_full_name')

class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    is_recent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id', 'team', 'team_name', 'user', 'activity_type',
            'description', 'metadata', 'created_at', 'is_recent'
        ]
        read_only_fields = fields