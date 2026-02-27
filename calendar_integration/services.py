import os
import json
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, user):
        self.user = user
        self.service = None
        self.credentials = None
        
    def get_authorization_url(self):
        """Get Google OAuth2 authorization URL"""
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
            }
        },
        scopes=self.SCOPES
)

        flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return authorization_url, state
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
            }
        },
        scopes=self.SCOPES
        )

        flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
        
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Save credentials to user's calendar sync
            from .models import CalendarSync
            sync, created = CalendarSync.objects.get_or_create(
                user=self.user,
                provider='google',
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'is_active': True
                }
            )
            
            if not created:
                sync.access_token = credentials.token
                sync.refresh_token = credentials.refresh_token
                sync.is_active = True
                sync.save()
            
            self.credentials = credentials
            self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return False
    
    def sync_calendar_events(self, days_future=30, days_past=7):
        """Sync events between Google Calendar and our system"""
        if not self.service:
            self._initialize_service()
        
        if not self.service:
            return False
        
        try:
            # Calculate time range
            now = timezone.now()
            time_min = (now - timedelta(days=days_past)).isoformat() + 'Z'
            time_max = (now + timedelta(days=days_future)).isoformat() + 'Z'
            
            # Get events from Google Calendar
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Sync events to our database
            from .models import CalendarEvent, CalendarSync
            calendar_sync = CalendarSync.objects.get(user=self.user, provider='google')
            
            synced_count = 0
            for event in events:
                # Skip all-day events for now
                if 'date' in event['start']:
                    continue
                
                # Create or update event
                calendar_event, created = CalendarEvent.objects.update_or_create(
                    external_event_id=event['id'],
                    calendar_sync=calendar_sync,
                    defaults={
                        'user': self.user,
                        'title': event.get('summary', 'Untitled Event'),
                        'description': event.get('description', ''),
                        'start_time': event['start']['dateTime'],
                        'end_time': event['end']['dateTime'],
                        'is_synced': True,
                        'color': event.get('colorId', '#3788d8'),
                    }
                )
                synced_count += 1
            
            # Update last sync time
            calendar_sync.last_sync = timezone.now()
            calendar_sync.save()
            
            return synced_count
            
        except HttpError as error:
            logger.error(f"Google Calendar API error: {error}")
            return False
    
    def create_event(self, event_data):
        """Create event in Google Calendar"""
        if not self.service:
            self._initialize_service()
        
        if not self.service:
            return None
        
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            return event
            
        except HttpError as error:
            logger.error(f"Error creating Google Calendar event: {error}")
            return None
    
    def _initialize_service(self):
        """Initialize Google Calendar service with stored credentials"""
        from .models import CalendarSync
        try:
            sync = CalendarSync.objects.get(user=self.user, provider='google', is_active=True)
            
            credentials = google.oauth2.credentials.Credentials(
                token=sync.access_token,
                refresh_token=sync.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
                client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
                scopes=self.SCOPES
            )
            
            self.credentials = credentials
            self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
            
        except CalendarSync.DoesNotExist:
            logger.error(f"No active Google Calendar sync found for user {self.user.username}")
    
    # def _get_client_secrets_path(self):
    #     """Get path to client secrets file"""
    #     return os.path.join(settings.BASE_DIR, 'client_secrets.json')

class CalendarManager:
    def __init__(self, user):
        self.user = user
    
    def get_upcoming_events(self, days=7):
        """Get upcoming events for the user"""
        from .models import CalendarEvent
        now = timezone.now()
        future = now + timedelta(days=days)
        
        return CalendarEvent.objects.filter(
            user=self.user,
            start_time__gte=now,
            start_time__lte=future
        ).order_by('start_time')
    
    def get_todays_events(self):
        """Get today's events"""
        from .models import CalendarEvent
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        return CalendarEvent.objects.filter(
            user=self.user,
            start_time__date=today
        ).order_by('start_time')
    
    def create_time_block(self, title, start_time, end_time, block_type='focus', tasks=None):
        """Create a time block for focused work"""
        from .models import TimeBlock
        time_block = TimeBlock.objects.create(
            user=self.user,
            title=title,
            start_time=start_time,
            end_time=end_time,
            block_type=block_type
        )
        
        if tasks:
            time_block.tasks.set(tasks)
        
        return time_block
    
    def find_available_slots(self, duration_hours=1, days_ahead=7):
        """Find available time slots for scheduling"""
        from .models import WorkingHours, CalendarEvent
        available_slots = []
        
        for day_offset in range(days_ahead):
            target_date = timezone.now().date() + timedelta(days=day_offset)
            day_of_week = target_date.weekday()
            
            try:
                working_hours = WorkingHours.objects.get(user=self.user, day_of_week=day_of_week)
                if not working_hours.is_working_day:
                    continue
                
                # Convert working hours to datetime for the target date
                work_start = timezone.make_aware(datetime.combine(target_date, working_hours.start_time))
                work_end = timezone.make_aware(datetime.combine(target_date, working_hours.end_time))
                
                # Get existing events for this day
                events = CalendarEvent.objects.filter(
                    user=self.user,
                    start_time__date=target_date,
                    is_busy=True
                ).order_by('start_time')
                
                # Find gaps between events
                current_time = work_start
                for event in events:
                    if event.start_time > current_time:
                        gap_duration = (event.start_time - current_time).total_seconds() / 3600
                        if gap_duration >= duration_hours:
                            available_slots.append({
                                'start': current_time,
                                'end': event.start_time,
                                'duration': gap_duration
                            })
                    current_time = max(current_time, event.end_time)
                
                # Check gap after last event
                if current_time < work_end:
                    gap_duration = (work_end - current_time).total_seconds() / 3600
                    if gap_duration >= duration_hours:
                        available_slots.append({
                            'start': current_time,
                            'end': work_end,
                            'duration': gap_duration
                        })
                        
            except WorkingHours.DoesNotExist:
                continue
        
        return available_slots
    
    def schedule_task(self, task, preferred_duration=None):
        """Automatically schedule a task in available time"""
        from tasks.models import Task
        
        if not preferred_duration:
            preferred_duration = task.estimated_hours or 1
        
        available_slots = self.find_available_slots(preferred_duration)
        
        if available_slots:
            # Use the first available slot
            slot = available_slots[0]
            
            # Create calendar event for the task
            from .models import CalendarEvent
            event = CalendarEvent.objects.create(
                user=self.user,
                title=f"Work on: {task.title}",
                description=task.description,
                event_type='task',
                start_time=slot['start'],
                end_time=slot['start'] + timedelta(hours=preferred_duration),
                task=task,
                color='#10b981'  # Green color for tasks
            )
            
            return event
        
        return None