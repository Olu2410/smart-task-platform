from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
import json

from .models import Task, Project, Comment, Attachment
from .forms import TaskForm, ProjectForm, CommentForm, AttachmentForm
from users.models import Team  



@login_required
def task_board(request):
    """Main kanban board view"""
    # Get teams the user is member of
    user_teams = Team.objects.filter(members=request.user)
    
    # Get projects from user's teams
    projects = Project.objects.filter(team__in=user_teams, is_active=True)
    
    # Get tasks organized by status
    tasks_by_status = {}
    for status_choice in Task.STATUS_CHOICES:
        status = status_choice[0]
        tasks = Task.objects.filter(
            project__team__in=user_teams,
            status=status
        ).select_related('assigned_to', 'project').order_by('order', '-priority')
        tasks_by_status[status] = tasks
    
    # Get statistics for dashboard
    total_tasks = Task.objects.filter(project__team__in=user_teams).count()
    pending_tasks = Task.objects.filter(
        project__team__in=user_teams,
        status__in=['todo', 'in_progress', 'review']
    ).count()
    completed_tasks = Task.objects.filter(
        project__team__in=user_teams,
        status='done'
    ).count()
    overdue_tasks = Task.objects.filter(
        project__team__in=user_teams,
        due_date__lt=timezone.now(),
        status__in=['todo', 'in_progress', 'review']
    ).count()
    
    return render(request, 'tasks/board.html', {
        'tasks_by_status': tasks_by_status,
        'status_choices': Task.STATUS_CHOICES,
        'projects': projects,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
    })

@login_required
def create_task(request):
    """Create a new task"""
    user_teams = Team.objects.filter(members=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            
            # Set order to be last in the column
            last_task = Task.objects.filter(
                project=task.project,
                status=task.status
            ).order_by('-order').first()
            task.order = (last_task.order + 1) if last_task else 0
            
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks:task_board')
    else:
        form = TaskForm(user=request.user)
    
    return render(request, 'tasks/create_task.html', {
        'form': form,
        'user_teams': user_teams,
    })

@login_required
def task_detail(request, pk):
    """View task details"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check if user has access to this task
    if not task.project.team.members.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this task.")
        return redirect('tasks:task_board')
    
    comments = Comment.objects.filter(task=task).select_related('user')
    attachments = Attachment.objects.filter(task=task)
    
    comment_form = CommentForm()
    attachment_form = AttachmentForm()
    
    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'comments': comments,
        'attachments': attachments,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
    })

@login_required
def update_task(request, pk):
    """Update an existing task"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check if user has permission to edit this task
    if not task.project.team.members.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to edit this task.")
        return redirect('tasks:task_board')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('tasks:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    
    return render(request, 'tasks/update_task.html', {
        'form': form,
        'task': task,
    })

@login_required
def delete_task(request, pk):
    """Delete a task"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check if user has permission to delete this task
    if task.created_by != request.user and not task.project.team.created_by == request.user:
        messages.error(request, "You don't have permission to delete this task.")
        return redirect('task_board')
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('tasks:task_board')
    
    return render(request, 'tasks/delete_task.html', {
        'task': task,
    })

@login_required
def project_list(request):
    """List all projects user has access to"""
    user_teams = Team.objects.filter(members=request.user)
    projects = Project.objects.filter(team__in=user_teams, is_active=True).annotate(
        task_count=Count('task'),
        completed_count=Count('task', filter=Q(task__status='done')),
        overdue_count=Count('task', filter=Q(task__due_date__lt=timezone.now()) & ~Q(task__status='done'))
    )
    
    return render(request, 'tasks/project_list.html', {
        'projects': projects,
    })

@login_required
def create_project(request):
    """Create a new project"""
    user_teams = Team.objects.filter(members=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            project = form.save()
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('tasks:project_detail', pk=project.pk)
    else:
        form = ProjectForm(user=request.user)
    
    return render(request, 'tasks/create_project.html', {
        'form': form,
        'user_teams': user_teams,
    })

@login_required
def project_detail(request, pk):
    """View project details"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check if user has access to this project
    if not project.team.members.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this project.")
        return redirect('tasks:project_list')
    
    # Get tasks for this project organized by status
    tasks_by_status = {}
    for status_choice in Task.STATUS_CHOICES:
        status = status_choice[0]
        tasks = Task.objects.filter(
            project=project,
            status=status
        ).select_related('assigned_to').order_by('order', '-priority')
        tasks_by_status[status] = tasks
    
    # Project statistics
    total_tasks = Task.objects.filter(project=project).count()
    completed_tasks = Task.objects.filter(project=project, status='done').count()
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return render(request, 'tasks/project_detail.html', {
        'project': project,
        'tasks_by_status': tasks_by_status,
        'status_choices': Task.STATUS_CHOICES,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'progress': progress,
    })

# Remove team_list and create_team views since they're in users app

@login_required
def update_task_status(request):
    """AJAX view to update task status (for drag & drop)"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            task_id = data.get('task_id')
            new_status = data.get('status')
            
            task = get_object_or_404(Task, pk=task_id)
            
            # Check if user has access to this task
            if not task.project.team.members.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Permission denied'})
            
            task.status = new_status
            task.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def reorder_tasks(request):
    """AJAX view to reorder tasks within a column"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            task_ids = data.get('task_ids', [])
            status = data.get('status')
            
            for order, task_id in enumerate(task_ids):
                task = get_object_or_404(Task, pk=task_id)
                
                # Check if user has access to this task
                if not task.project.team.members.filter(id=request.user.id).exists():
                    continue
                
                task.status = status
                task.order = order
                task.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def add_comment(request, task_id):
    """Add a comment to a task"""
    task = get_object_or_404(Task, pk=task_id)
    
    # Check if user has access to this task
    if not task.project.team.members.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to comment on this task.")
        return redirect('tasks:task_board')
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            
            messages.success(request, 'Comment added successfully!')
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def add_attachment(request, task_id):
    """Add an attachment to a task"""
    task = get_object_or_404(Task, pk=task_id)
    
    # Check if user has access to this task
    if not task.project.team.members.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to add attachments to this task.")
        return redirect('tasks:task_board')
    
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.uploaded_by = request.user
            attachment.filename = attachment.file.name
            attachment.save()
            
            messages.success(request, 'File uploaded successfully!')
    
    return redirect('tasks:task_detail', pk=task_id)