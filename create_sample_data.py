import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Team, TeamMembership
from tasks.models import Project, Task, Comment
from django.utils import timezone
from datetime import timedelta

def create_sample_comments():
    """Add sample comments to tasks"""
    User = get_user_model()
    tasks = Task.objects.all()
    users = User.objects.all()
    
    sample_comments = [
        "Great progress on this task!",
        "Can you provide more details about the requirements?",
        "I've completed the initial implementation.",
        "This is blocked by the design assets.",
        "Let's discuss this in our next meeting.",
        "The deadline might need to be adjusted.",
        "I need access to the API documentation.",
        "This is ready for review.",
        "Found a bug that needs fixing.",
        "Can we pair on this tomorrow?"
    ]
    
    for task in tasks:
        # Add 2-3 random comments to each task
        import random
        num_comments = random.randint(2, 3)
        for _ in range(num_comments):
            user = random.choice(users)
            comment_text = random.choice(sample_comments)
            Comment.objects.create(
                task=task,
                user=user,
                content=comment_text
            )
    
    print(f"Created sample comments for {tasks.count()} tasks")

if __name__ == '__main__':
    create_sample_comments()