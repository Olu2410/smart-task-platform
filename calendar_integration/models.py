from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class CalendarSync(models.Model):
    CALENDAR_PROVIDERS = [
        ('google', 'Google Calendar'),
        ('outlook', 'Microsoft Outlook'),
        ('apple', 'Apple Calendar'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_syncs')
    provider = models.CharField(max_length=50, choices=CALENDAR_PROVIDERS)
    is_active = models.BooleanField(default=True)
    access_token = models.TextField(blank=True)
    refresh_token = models.TextField(blank=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    calendar_id = models.CharField(max_length=255, blank=True)  # Specific calendar ID
    sync_future_days = models.IntegerField(default=30)  # How many days ahead to sync
    sync_past_days = models.IntegerField(default=7)     # How many days back to sync
    
    class Meta:
        unique_together = ['user', 'provider']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_provider_display()}"

class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('task', 'Task'),
        ('meeting', 'Meeting'),
        ('focus_block', 'Focus Time'),
        ('break', 'Break'),
        ('personal', 'Personal'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, default='task')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_all_day = models.BooleanField(default=False)
    
    # Task association (if this event is for a task)
    task = models.ForeignKey('tasks.Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_events')
    
    # External calendar integration
    external_event_id = models.CharField(max_length=255, blank=True)  # ID from Google/Outlook
    calendar_sync = models.ForeignKey(CalendarSync, on_delete=models.CASCADE, null=True, blank=True)
    is_synced = models.BooleanField(default=False)
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.TextField(blank=True)  # Store RRULE for recurring events
    
    # Colors and styling
    color = models.CharField(max_length=7, default='#3788d8')  # Hex color
    is_busy = models.BooleanField(default=True)  # Show as busy in calendars
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['user', 'start_time', 'end_time']),
            models.Index(fields=['task']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    @property
    def duration(self):
        """Calculate event duration in hours"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() / 3600  # Convert to hours
        return 0
    
    def is_current(self):
        """Check if event is currently happening"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time
    
    def is_upcoming(self, hours=24):
        """Check if event starts within the next X hours"""
        now = timezone.now()
        future_limit = now + timedelta(hours=hours)
        return self.start_time >= now and self.start_time <= future_limit

class TimeBlock(models.Model):
    """Represents blocked time for focused work"""
    BLOCK_TYPES = [
        ('focus', 'Focus Time'),
        ('meeting', 'Meeting Block'),
        ('break', 'Break'),
        ('learning', 'Learning'),
        ('admin', 'Administrative'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_blocks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPES, default='focus')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Associated tasks for this time block
    tasks = models.ManyToManyField('tasks.Task', blank=True, related_name='time_blocks')
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_days = models.CharField(max_length=50, blank=True)  # e.g., "monday,wednesday,friday"
    
    color = models.CharField(max_length=7, default='#3788d8')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class WorkingHours(models.Model):
    """User's preferred working hours by day"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='working_hours')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working_day = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'day_of_week']
        ordering = ['day_of_week']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_day_of_week_display()}"

class MeetingSlot(models.Model):
    """Available meeting slots for scheduling"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meeting_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    max_meetings_per_slot = models.IntegerField(default=1)
    current_meetings_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"Meeting slot - {self.user.username} - {self.start_time}"



#OLD CODE - DO NOT DELETE

# # Create your models here.
# from django.db import models
# from django.conf import settings

# class CalendarSync(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     provider = models.CharField(max_length=50)  # 'google', 'outlook', etc.
#     is_active = models.BooleanField(default=True)
#     access_token = models.TextField(blank=True)
#     refresh_token = models.TextField(blank=True)
#     last_sync = models.DateTimeField(null=True, blank=True)
    
#     def __str__(self):
#         return f"{self.user.username} - {self.provider}"