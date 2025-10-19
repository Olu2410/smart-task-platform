
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django_countries.fields import CountryField
from timezone_field import TimeZoneField

class CustomUser(AbstractUser):
    # Personal Information
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Professional Information
    job_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    # Location & Time
    timezone = TimeZoneField(default='UTC')
    country = CountryField(blank=True)
    
    # Avatar/Profile Picture
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Preferences
    email_notifications = models.BooleanField(default=True)
    desktop_notifications = models.BooleanField(default=True)
    daily_digest = models.BooleanField(default=True)
    
    # Work Hours
    workday_start = models.TimeField(default='09:00')
    workday_end = models.TimeField(default='17:00')
    working_days = models.CharField(
        max_length=13, 
        default='monday,tuesday,wednesday,thursday,friday',
        help_text="Comma-separated list of working days"
    )
    
    # AI Preferences
    ai_task_suggestions = models.BooleanField(default=True)
    ai_time_optimization = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
    
    def get_working_days_list(self):
        return [day.strip() for day in self.working_days.split(',')]
    
    @property
    def display_name(self):
        return self.get_full_name() or self.username

class UserAvailability(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_working_day = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'day_of_week']
        ordering = ['day_of_week', 'start_time']

class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_teams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Team settings
    is_public = models.BooleanField(default=False)
    allow_self_join = models.BooleanField(default=False)
    
    # Members
    members = models.ManyToManyField(CustomUser, through='TeamMembership', related_name='teams')
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        return self.members.count()
    
    def is_user_member(self, user):
        return self.members.filter(id=user.id).exists()

class TeamMembership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'team']
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"

class Invitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    email = models.EmailField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    invited_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_invitations')
    token = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=20, choices=TeamMembership.ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.team.name}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at