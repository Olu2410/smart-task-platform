from django import template
from ..models import Project

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get dictionary item by key"""
    return dictionary.get(key, [])


@register.simple_tag
def get_team_projects(team):
    """Get all projects for a team"""
    return Project.objects.filter(team=team, is_active=True)