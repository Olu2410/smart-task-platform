import openai
import json
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from tasks.models import Task, Project
from users.models import Team, UserAvailability
from .models import AISuggestion

logger = logging.getLogger(__name__)

class AICoachService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    def analyze_task_priority(self, task):
        """Analyze task and suggest optimal priority"""
        if not self.client:
            logger.warning("OpenAI API key not configured")
            return self._get_fallback_priority_suggestion(task)
        
        try:
            prompt = self._build_priority_analysis_prompt(task)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_priority_response(result, task)
            
        except Exception as e:
            logger.error(f"AI priority analysis failed: {e}")
            return self._get_fallback_priority_suggestion(task)
    
    def suggest_task_timing(self, task, user):
        """Suggest optimal timing for task completion"""
        if not self.client:
            return self._get_fallback_timing_suggestion(task, user)
        
        try:
            prompt = self._build_timing_analysis_prompt(task, user)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.4
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_timing_response(result, task)
            
        except Exception as e:
            logger.error(f"AI timing analysis failed: {e}")
            return self._get_fallback_timing_suggestion(task, user)
    
    def analyze_workload_balance(self, team):
        """Analyze workload distribution across team members"""
        if not self.client:
            return self._get_fallback_workload_analysis(team)
        
        try:
            prompt = self._build_workload_analysis_prompt(team)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_workload_response(result, team)
            
        except Exception as e:
            logger.error(f"AI workload analysis failed: {e}")
            return self._get_fallback_workload_analysis(team)
    
    def generate_weekly_plan(self, user):
        """Generate AI-powered weekly plan"""
        upcoming_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress'],
            due_date__lte=timezone.now() + timedelta(days=14)
        ).select_related('project')
        
        if not self.client:
            return self._get_fallback_weekly_plan(upcoming_tasks)
        
        try:
            prompt = self._build_weekly_plan_prompt(user, upcoming_tasks)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.4
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_weekly_plan_response(result, upcoming_tasks)
            
        except Exception as e:
            logger.error(f"AI weekly plan generation failed: {e}")
            return self._get_fallback_weekly_plan(upcoming_tasks)
    
    def apply_suggestion(self, suggestion):
        """Apply an AI suggestion to the actual task"""
        try:
            task = suggestion.task
            
            if suggestion.suggestion_type == 'priority':
                # Extract priority from suggestion
                if 'urgent' in suggestion.suggestion.lower():
                    task.priority = 'urgent'
                elif 'high' in suggestion.suggestion.lower():
                    task.priority = 'high'
                elif 'medium' in suggestion.suggestion.lower():
                    task.priority = 'medium'
                elif 'low' in suggestion.suggestion.lower():
                    task.priority = 'low'
                task.save()
                return True
                
            elif suggestion.suggestion_type == 'timing':
                # Parse suggested timing
                # This would update due_date or create calendar events
                # For now, we'll just mark as applied
                return True
                
            elif suggestion.suggestion_type == 'workload':
                # Workload suggestions are informational
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply suggestion: {e}")
            return False
        
        return False

    # Prompt Building Methods
    def _build_priority_analysis_prompt(self, task):
        return f"""
        Analyze this task and provide a priority recommendation with reasoning:

        TASK DETAILS:
        - Title: {task.title}
        - Description: {task.description or "No description"}
        - Current Priority: {task.get_priority_display()}
        - Due Date: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not set'}
        - Project: {task.project.name}
        - Status: {task.get_status_display()}
        - Estimated Hours: {task.estimated_hours or 'Not estimated'}

        CONSIDER:
        - Urgency based on due date proximity
        - Importance based on project and task content
        - Complexity from description and estimated hours
        - Current status and progress

        RESPONSE FORMAT (JSON):
        {{
            "recommended_priority": "low|medium|high|urgent",
            "confidence_score": 0.0-1.0,
            "reasoning": "Detailed explanation",
            "suggested_actions": ["action1", "action2"]
        }}

        Be specific and practical in your recommendations.
        """

    def _build_timing_analysis_prompt(self, task, user):
        user_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress'],
            due_date__isnull=False
        ).exclude(id=task.id)[:10]
        
        tasks_context = "\n".join([
            f"- {t.title} (Due: {t.due_date.strftime('%Y-%m-%d')}, Priority: {t.priority})"
            for t in user_tasks
        ])
        
        return f"""
        Analyze optimal timing for this task considering the user's schedule:

        TASK TO SCHEDULE:
        - Title: {task.title}
        - Description: {task.description or "No description"}
        - Priority: {task.get_priority_display()}
        - Estimated Hours: {task.estimated_hours or 'Not estimated'}
        - Current Due Date: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Not set'}

        USER'S OTHER TASKS:
        {tasks_context}

        USER'S WORK PREFERENCES:
        - Work Hours: {user.workday_start.strftime('%H:%M') if user.workday_start else '09:00'} - {user.workday_end.strftime('%H:%M') if user.workday_end else '17:00'}
        - Working Days: {user.working_days}

        RECOMMEND:
        - Ideal start date
        - Suggested due date adjustment if needed
        - Time blocking recommendations

        RESPONSE FORMAT (JSON):
        {{
            "ideal_start_date": "YYYY-MM-DD",
            "suggested_due_date": "YYYY-MM-DD",
            "reasoning": "Explanation",
            "time_blocks_needed": number,
            "scheduling_notes": ["note1", "note2"]
        }}
        """

    def _build_workload_analysis_prompt(self, team):
        team_members = team.members.all()
        workload_data = []
        
        for member in team_members:
            tasks = Task.objects.filter(
                assigned_to=member,
                status__in=['todo', 'in_progress']
            )
            total_tasks = tasks.count()
            high_priority = tasks.filter(priority__in=['high', 'urgent']).count()
            overdue = tasks.filter(due_date__lt=timezone.now()).count()
            
            workload_data.append({
                'member': member.get_full_name() or member.username,
                'total_tasks': total_tasks,
                'high_priority_tasks': high_priority,
                'overdue_tasks': overdue
            })
        
        workload_context = "\n".join([
            f"- {data['member']}: {data['total_tasks']} tasks ({data['high_priority_tasks']} high priority, {data['overdue_tasks']} overdue)"
            for data in workload_data
        ])
        
        return f"""
        Analyze workload distribution for this team and provide recommendations:

        TEAM: {team.name}
        
        CURRENT WORKLOAD DISTRIBUTION:
        {workload_context}

        ANALYZE:
        - Workload balance across team members
        - Potential bottlenecks or overloaded members
        - Priority distribution issues
        - Overdue task patterns

        PROVIDE:
        - Balance assessment
        - Specific recommendations for redistribution
        - Priority adjustments if needed
        - Team capacity insights

        RESPONSE FORMAT (JSON):
        {{
            "balance_assessment": "balanced|moderately_imbalanced|severely_imbalanced",
            "overloaded_members": ["member1", "member2"],
            "underutilized_members": ["member1", "member2"],
            "recommendations": [
                {{
                    "type": "redistribution|priority_adjustment|deadline_adjustment",
                    "description": "Specific action",
                    "impact": "high|medium|low"
                }}
            ],
            "overall_insights": "Summary of findings"
        }}
        """

    def _build_weekly_plan_prompt(self, user, tasks):
        tasks_context = "\n".join([
            f"- {task.title} (Priority: {task.priority}, Due: {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'No due date'}, Est: {task.estimated_hours or '?'}h)"
            for task in tasks
        ])
        
        return f"""
        Create an optimal weekly plan for this user:

        USER PREFERENCES:
        - Work Hours: {user.workday_start.strftime('%H:%M') if user.workday_start else '09:00'} - {user.workday_end.strftime('%H:%M') if user.workday_end else '17:00'}
        - Working Days: {user.working_days}

        UPCOMING TASKS:
        {tasks_context}

        CREATE A WEEKLY PLAN THAT:
        - Prioritizes urgent and high-priority tasks
        - Considers due dates and estimated effort
        - Balances workload across the week
        - Includes time for deep work and breaks
        - Accounts for task dependencies and context switching

        RESPONSE FORMAT (JSON):
        {{
            "weekly_focus": "Overall theme or goal for the week",
            "daily_plans": {{
                "monday": {{
                    "focus": "Primary focus for the day",
                    "tasks": ["task1", "task2"],
                    "time_blocks": [
                        {{
                            "time": "09:00-11:00",
                            "activity": "Deep work on task X",
                            "priority": "high"
                        }}
                    ]
                }}
            }},
            "key_priorities": ["priority1", "priority2"],
            "risk_warnings": ["warning1", "warning2"]
        }}
        """

    # Response Parsing Methods
    def _parse_priority_response(self, response, task):
        try:
            data = json.loads(response)
            
            # Create suggestion record
            suggestion = AISuggestion.objects.create(
                task=task,
                suggestion_type='priority',
                suggestion=f"Change priority to {data['recommended_priority'].title()}",
                reasoning=data['reasoning'],
                confidence_score=float(data['confidence_score']),
                metadata={
                    'suggested_actions': data.get('suggested_actions', []),
                    'current_priority': task.priority
                }
            )
            
            return {
                'success': True,
                'suggestion_id': suggestion.id,
                'recommended_priority': data['recommended_priority'],
                'confidence': data['confidence_score'],
                'reasoning': data['reasoning'],
                'suggested_actions': data.get('suggested_actions', [])
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse priority response: {e}")
            return self._get_fallback_priority_suggestion(task)

    def _parse_timing_response(self, response, task):
        try:
            data = json.loads(response)
            
            suggestion = AISuggestion.objects.create(
                task=task,
                suggestion_type='timing',
                suggestion=f"Schedule task: Start {data['ideal_start_date']}, Due {data['suggested_due_date']}",
                reasoning=data['reasoning'],
                confidence_score=0.8,
                metadata={
                    'ideal_start_date': data['ideal_start_date'],
                    'suggested_due_date': data['suggested_due_date'],
                    'time_blocks_needed': data.get('time_blocks_needed', 1),
                    'scheduling_notes': data.get('scheduling_notes', [])
                }
            )
            
            return {
                'success': True,
                'suggestion_id': suggestion.id,
                'ideal_start_date': data['ideal_start_date'],
                'suggested_due_date': data['suggested_due_date'],
                'reasoning': data['reasoning']
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse timing response: {e}")
            return self._get_fallback_timing_suggestion(task, task.assigned_to)

    # Fallback methods for when AI is not available
    def _get_fallback_priority_suggestion(self, task):
        # Simple rule-based fallback
        if task.due_date and (task.due_date - timezone.now()).days <= 1:
            recommended_priority = 'high'
            confidence = 0.7
            reasoning = "Task is due soon"
        elif 'urgent' in task.title.lower() or 'critical' in task.title.lower():
            recommended_priority = 'urgent'
            confidence = 0.6
            reasoning = "Task title indicates urgency"
        else:
            recommended_priority = 'medium'
            confidence = 0.5
            reasoning = "Standard priority based on available information"
        
        suggestion = AISuggestion.objects.create(
            task=task,
            suggestion_type='priority',
            suggestion=f"Change priority to {recommended_priority.title()}",
            reasoning=reasoning,
            confidence_score=confidence
        )
        
        return {
            'success': True,
            'suggestion_id': suggestion.id,
            'recommended_priority': recommended_priority,
            'confidence': confidence,
            'reasoning': reasoning,
            'suggested_actions': ['Review due date', 'Break down if complex']
        }

    def _get_fallback_timing_suggestion(self, task, user):
        # Simple fallback timing logic
        if task.due_date:
            ideal_start = task.due_date - timedelta(days=2)
        else:
            ideal_start = timezone.now() + timedelta(days=1)
        
        suggestion = AISuggestion.objects.create(
            task=task,
            suggestion_type='timing',
            suggestion=f"Start by {ideal_start.strftime('%Y-%m-%d')}",
            reasoning="Based on standard task scheduling",
            confidence_score=0.6
        )
        
        return {
            'success': True,
            'suggestion_id': suggestion.id,
            'ideal_start_date': ideal_start.strftime('%Y-%m-%d'),
            'suggested_due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
            'reasoning': "Standard scheduling recommendation"
        }

    def _get_fallback_workload_analysis(self, team):
        return {
            'success': True,
            'balance_assessment': 'moderately_imbalanced',
            'overloaded_members': [],
            'underutilized_members': [],
            'recommendations': [
                {
                    'type': 'general',
                    'description': 'Review task distribution manually',
                    'impact': 'medium'
                }
            ],
            'overall_insights': 'Basic workload analysis completed'
        }

    def _get_fallback_weekly_plan(self, tasks):
        high_priority_tasks = [t for t in tasks if t.priority in ['high', 'urgent']]
        other_tasks = [t for t in tasks if t.priority not in ['high', 'urgent']]
        
        return {
            'success': True,
            'weekly_focus': 'Complete high-priority tasks first',
            'daily_plans': {},
            'key_priorities': [t.title for t in high_priority_tasks[:3]],
            'risk_warnings': ['Consider task dependencies', 'Watch for context switching']
        }






# import openai
# from datetime import datetime, timedelta
# from django.conf import settings
# from tasks.models import Task, TimeSlot
# # from .models import AISuggestion
# import logging

# logger = logging.getLogger(__name__)

# class AICoachService:
#     def __init__(self):
#         # Initialize with your OpenAI API key
#         self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
#     def analyze_task_priority(self, task):
#         """Analyze task and suggest priority based on content and context"""
#         prompt = f"""
#         Analyze this task and suggest appropriate priority (low, medium, high, urgent):
        
#         Task: {task.title}
#         Description: {task.description}
#         Due Date: {task.due_date}
#         Project: {task.project.name}
        
#         Consider:
#         - Urgency based on due date
#         - Importance based on task content
#         - Complexity based on description
        
#         Return only the priority level (low, medium, high, urgent) and a brief reason.
#         Format: priority|reason
#         """
        
#         try:
#             response = self.client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[{"role": "user", "content": prompt}],
#                 max_tokens=100
#             )
            
#             result = response.choices[0].message.content.strip()
#             priority, reason = result.split('|', 1)
            
#             return {
#                 'priority': priority.strip().lower(),
#                 'reason': reason.strip(),
#                 'confidence': 0.85
#             }
#         except Exception as e:
#             logger.error(f"AI priority analysis failed: {e}")
#             return None
    
#     def suggest_task_timing(self, task, user_tasks):
#         """Suggest optimal timing for task completion"""
#         # Analyze user's existing schedule and task dependencies
#         busy_slots = TimeSlot.objects.filter(
#             user=task.assigned_to,
#             start_time__gte=datetime.now()
#         )
        
#         prompt = f"""
#         Suggest optimal timing for this task considering:
#         - Task: {task.title}
#         - Estimated hours: {task.estimated_hours}
#         - Due date: {task.due_date}
#         - User's current workload
        
#         Return suggested start date and time in format: YYYY-MM-DD HH:MM|reason
#         """
        
#         # Implementation similar to analyze_task_priority
#         # ...
    
#     def generate_weekly_plan(self, user, team):
#         """Generate weekly plan with AI suggestions"""
#         upcoming_tasks = Task.objects.filter(
#             assigned_to=user,
#             status__in=['todo', 'in_progress'],
#             due_date__lte=datetime.now() + timedelta(days=7)
#         )
        
#         # AI logic to create optimal weekly schedule
#         # ...
#     def analyze_team_workload(self, user):
#         """Analyze workload distribution across team"""
#         # Placeholder implementation
#         return {
#             'analysis': "Workload appears balanced across the team",
#             'recommendations': ["Consider redistributing some tasks from overloaded members"]
#         }