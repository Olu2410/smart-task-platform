from django import forms
from .models import Task, Project, Comment, Attachment
from users.models import Team 

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'project', 'assigned_to', 'due_date', 
                 'priority', 'status', 'estimated_hours', 'tags']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter projects to only those the user has access to
            user_teams = Team.objects.filter(members=self.user)
            self.fields['project'].queryset = Project.objects.filter(team__in=user_teams)
            
            # Filter assignable users to team members
            if self.instance and self.instance.pk:
                # For existing task, use project's team members
                project = self.instance.project
            else:
                # For new task, we'll set this after project is chosen
                project = None
            
            if project:
                self.fields['assigned_to'].queryset = project.team.members.all()
            else:
                self.fields['assigned_to'].queryset = self.user.teams.none()
            
            # Add JavaScript for dynamic filtering
            self.fields['project'].widget.attrs.update({
                'onchange': 'updateAssignableUsers(this.value)'
            })

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'team', 'color']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filter teams to only those the user is member of
            self.fields['team'].queryset = Team.objects.filter(members=self.user)

# Remove TeamForm since it's now in users app
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...'}),
        }

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }