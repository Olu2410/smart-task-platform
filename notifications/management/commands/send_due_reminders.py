# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from tasks.models import Task
# from notifications.services import NotificationService

# class Command(BaseCommand):
#     help = 'Send notifications for due and overdue tasks'
    
#     def handle(self, *args, **options):
#         now = timezone.now()
        
#         # Tasks due in next 24 hours
#         due_soon = Task.objects.filter(
#             due_date__gt=now,
#             due_date__lte=now + timezone.timedelta(hours=24),
#             completed=False
#         )
        
#         for task in due_soon:
#             NotificationService.notify_task_due(task)
        
#         # Overdue tasks
#         overdue = Task.objects.filter(
#             due_date__lt=now,
#             completed=False
#         )
        
#         for task in overdue:
#             NotificationService.create_notification(
#                 user=task.assigned_to,
#                 notification_type='task_overdue',
#                 title='Task Overdue',
#                 message=f'Task "{task.title}" is overdue',
#                 related_object=task
#             )
        
#         self.stdout.write(
#             self.style.SUCCESS(
#                 f'Sent {due_soon.count()} due soon and {overdue.count()} overdue notifications'
#             )
#         )