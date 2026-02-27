# team_chat/templatetags/team_chat_tags.py
from django import template
from ..models import TeamChannel

register = template.Library()

@register.simple_tag
def get_team_channels(team):
    """Get all channels for a team"""
    return TeamChannel.objects.filter(team=team).order_by('name')

@register.simple_tag
def get_recent_channel_messages(channel, limit=5):
    """Get recent messages for a channel"""
    return channel.messages.all().order_by('-created_at')[:limit]

@register.filter
def channel_message_count(channel):
    """Get message count for a channel"""
    return channel.messages.count()