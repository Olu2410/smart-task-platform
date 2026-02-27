from django.contrib import admin

# Register your models here.
from .models import Activity

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'activity_type', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__username', 'team__name', 'description']
    readonly_fields = ['created_at']