from django.db import models
from django.conf import settings

# Create your models here.

class AISuggestion(models.Model):
    SUGGESTION_TYPES = [
        ('priority', 'Priority Adjustment'),
        ('timing', 'Timing Suggestion'),
        ('assignment', 'Task Assignment'),
        ('deadline', 'Deadline Adjustment'),
        ('breakdown', 'Task Breakdown'),
    ]
    
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE)
    suggestion_type = models.CharField(max_length=50, choices=SUGGESTION_TYPES)
    suggestion = models.TextField()
    reasoning = models.TextField(blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_applied = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-confidence_score', '-created_at']
    
    def __str__(self):
        return f"{self.get_suggestion_type_display()} for {self.task.title}"