from django.contrib import admin

# Register your models here.
from .models import TeamChannel, ChannelMessage, FileShare

@admin.register(TeamChannel)
class TeamChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'is_private', 'created_by', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['name', 'team__name']

@admin.register(ChannelMessage)
class ChannelMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'channel', 'message_type', 'created_at']
    list_filter = ['message_type', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(FileShare)
class FileShareAdmin(admin.ModelAdmin):
    list_display = ['filename', 'team', 'file_type', 'file_size_mb', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'is_public', 'created_at']
    search_fields = ['filename', 'team__name']