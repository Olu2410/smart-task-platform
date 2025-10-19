import openai
from datetime import datetime, timedelta
from django.conf import settings
from tasks.models import Task, TimeSlot
# from .models import AISuggestion
import logging

logger = logging.getLogger(__name__)

class AICoachService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def analyze_task_priority(self, task):
        """Analyze task and suggest priority based on content and context"""
        prompt = f"""
        Analyze this task and suggest appropriate priority (low, medium, high, urgent):
        
        Task: {task.title}
        Description: {task.description}
        Due Date: {task.due_date}
        Project: {task.project.name}
        
        Consider:
        - Urgency based on due date
        - Importance based on task content
        - Complexity based on description
        
        Return only the priority level (low, medium, high, urgent) and a brief reason.
        Format: priority|reason
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            priority, reason = result.split('|', 1)
            
            return {
                'priority': priority.strip().lower(),
                'reason': reason.strip(),
                'confidence': 0.85
            }
        except Exception as e:
            logger.error(f"AI priority analysis failed: {e}")
            return None
    
    def suggest_task_timing(self, task, user_tasks):
        """Suggest optimal timing for task completion"""
        # Analyze user's existing schedule and task dependencies
        busy_slots = TimeSlot.objects.filter(
            user=task.assigned_to,
            start_time__gte=datetime.now()
        )
        
        prompt = f"""
        Suggest optimal timing for this task considering:
        - Task: {task.title}
        - Estimated hours: {task.estimated_hours}
        - Due date: {task.due_date}
        - User's current workload
        
        Return suggested start date and time in format: YYYY-MM-DD HH:MM|reason
        """
        
        # Implementation similar to analyze_task_priority
        # ...
    
    def generate_weekly_plan(self, user, team):
        """Generate weekly plan with AI suggestions"""
        upcoming_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress'],
            due_date__lte=datetime.now() + timedelta(days=7)
        )
        
        # AI logic to create optimal weekly schedule
        # ...
        