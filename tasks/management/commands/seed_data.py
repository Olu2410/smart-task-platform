from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Team, TeamMembership
from tasks.models import Project, Task
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database with sample data...')
        
        # Create users
        users = self.create_users()
        
        # Create teams
        teams = self.create_teams(users)
        
        # Create projects
        projects = self.create_projects(teams)
        
        # Create tasks
        self.create_tasks(projects, users)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with sample data!')
        )

    def create_users(self):
        users = []
        
        # Create admin user if not exists
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smarttask.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            users.append(admin_user)
            self.stdout.write(f'Created admin user: {admin_user.username}')
        
        # Create sample users
        sample_users = [
            {
                'username': 'alice',
                'email': 'alice@smarttask.com',
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'job_title': 'Project Manager',
                'department': 'Management'
            },
            {
                'username': 'bob',
                'email': 'bob@smarttask.com',
                'first_name': 'Bob',
                'last_name': 'Smith',
                'job_title': 'Frontend Developer',
                'department': 'Engineering'
            },
            {
                'username': 'carol',
                'email': 'carol@smarttask.com',
                'first_name': 'Carol',
                'last_name': 'Williams',
                'job_title': 'Backend Developer',
                'department': 'Engineering'
            },
            {
                'username': 'david',
                'email': 'david@smarttask.com',
                'first_name': 'David',
                'last_name': 'Brown',
                'job_title': 'UI/UX Designer',
                'department': 'Design'
            }
        ]
        
        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password('password123')
                user.save()
                users.append(user)
                self.stdout.write(f'Created user: {user.username}')
        
        return users

    def create_teams(self, users):
        teams = []
        
        sample_teams = [
            {
                'name': 'Development Team',
                'description': 'Main software development team',
                'is_public': True,
                'allow_self_join': False
            },
            {
                'name': 'Design Team',
                'description': 'UI/UX design team',
                'is_public': True,
                'allow_self_join': False
            },
            {
                'name': 'Marketing Team',
                'description': 'Marketing and outreach team',
                'is_public': False,
                'allow_self_join': True
            }
        ]
        
        for team_data in sample_teams:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults={
                    'description': team_data['description'],
                    'is_public': team_data['is_public'],
                    'allow_self_join': team_data['allow_self_join'],
                    'created_by': users[0]  # admin user
                }
            )
            if created:
                teams.append(team)
                self.stdout.write(f'Created team: {team.name}')
                
                # Add members to teams
                if team.name == 'Development Team':
                    # Add Alice, Bob, Carol to Development Team
                    for user in users[1:4]:  # Alice, Bob, Carol
                        TeamMembership.objects.create(
                            user=user,
                            team=team,
                            role='member' if user.username != 'alice' else 'manager'
                        )
                elif team.name == 'Design Team':
                    # Add David to Design Team
                    TeamMembership.objects.create(
                        user=users[4],  # David
                        team=team,
                        role='admin'
                    )
                elif team.name == 'Marketing Team':
                    # Add Alice to Marketing Team
                    TeamMembership.objects.create(
                        user=users[1],  # Alice
                        team=team,
                        role='manager'
                    )
        
        return teams

    def create_projects(self, teams):
        projects = []
        
        sample_projects = [
            {
                'name': 'Website Redesign',
                'description': 'Complete redesign of company website with modern UI/UX',
                'team': teams[0],  # Development Team
                'color': '#3498db'
            },
            {
                'name': 'Mobile App Development',
                'description': 'Build a cross-platform mobile application',
                'team': teams[0],  # Development Team
                'color': '#e74c3c'
            },
            {
                'name': 'Brand Identity',
                'description': 'Create new brand guidelines and design system',
                'team': teams[1],  # Design Team
                'color': '#9b59b6'
            },
            {
                'name': 'Q4 Marketing Campaign',
                'description': 'Launch holiday marketing campaign across all channels',
                'team': teams[2],  # Marketing Team
                'color': '#f39c12'
            }
        ]
        
        for project_data in sample_projects:
            project, created = Project.objects.get_or_create(
                name=project_data['name'],
                team=project_data['team'],
                defaults={
                    'description': project_data['description'],
                    'color': project_data['color']
                }
            )
            if created:
                projects.append(project)
                self.stdout.write(f'Created project: {project.name}')
        
        return projects

    def create_tasks(self, projects, users):
        now = timezone.now()
        
        sample_tasks = [
            # Website Redesign Project
            {
                'title': 'Create wireframes for homepage',
                'description': 'Design initial wireframes for the new homepage layout',
                'project': projects[0],
                'assigned_to': users[4],  # David (Designer)
                'due_date': now + timedelta(days=3),
                'priority': 'high',
                'status': 'in_progress',
                'estimated_hours': 8,
                'tags': 'design,wireframes'
            },
            {
                'title': 'Set up development environment',
                'description': 'Configure local development environment with all necessary tools',
                'project': projects[0],
                'assigned_to': users[2],  # Bob (Frontend)
                'due_date': now + timedelta(days=1),
                'priority': 'medium',
                'status': 'done',
                'estimated_hours': 4,
                'tags': 'development,setup'
            },
            {
                'title': 'Research competitor websites',
                'description': 'Analyze competitor websites for design inspiration and best practices',
                'project': projects[0],
                'assigned_to': users[1],  # Alice (PM)
                'due_date': now + timedelta(days=2),
                'priority': 'medium',
                'status': 'todo',
                'estimated_hours': 6,
                'tags': 'research,analysis'
            },
            
            # Mobile App Development Project
            {
                'title': 'Design app icon',
                'description': 'Create multiple versions of the app icon for different platforms',
                'project': projects[1],
                'assigned_to': users[4],  # David (Designer)
                'due_date': now + timedelta(days=5),
                'priority': 'medium',
                'status': 'todo',
                'estimated_hours': 4,
                'tags': 'design,icon'
            },
            {
                'title': 'Set up React Native project',
                'description': 'Initialize React Native project with required dependencies',
                'project': projects[1],
                'assigned_to': users[2],  # Bob (Frontend)
                'due_date': now + timedelta(days=2),
                'priority': 'high',
                'status': 'in_progress',
                'estimated_hours': 6,
                'tags': 'development,react-native'
            },
            {
                'title': 'Design database schema',
                'description': 'Create database schema for user data and app content',
                'project': projects[1],
                'assigned_to': users[3],  # Carol (Backend)
                'due_date': now + timedelta(days=4),
                'priority': 'high',
                'status': 'review',
                'estimated_hours': 8,
                'tags': 'backend,database'
            },
            
            # Brand Identity Project
            {
                'title': 'Create color palette',
                'description': 'Develop a cohesive color palette that reflects our brand values',
                'project': projects[2],
                'assigned_to': users[4],  # David (Designer)
                'due_date': now + timedelta(days=2),
                'priority': 'high',
                'status': 'done',
                'estimated_hours': 3,
                'tags': 'design,branding'
            },
            {
                'title': 'Design logo variations',
                'description': 'Create multiple logo variations for different use cases',
                'project': projects[2],
                'assigned_to': users[4],  # David (Designer)
                'due_date': now + timedelta(days=7),
                'priority': 'medium',
                'status': 'in_progress',
                'estimated_hours': 12,
                'tags': 'design,logo'
            },
            
            # Marketing Campaign Project
            {
                'title': 'Create social media calendar',
                'description': 'Plan and schedule social media posts for the campaign',
                'project': projects[3],
                'assigned_to': users[1],  # Alice (PM)
                'due_date': now + timedelta(days=10),
                'priority': 'medium',
                'status': 'todo',
                'estimated_hours': 8,
                'tags': 'marketing,social-media'
            },
            {
                'title': 'Write campaign email copy',
                'description': 'Draft email templates for the marketing campaign',
                'project': projects[3],
                'assigned_to': users[1],  # Alice (PM)
                'due_date': now + timedelta(days=8),
                'priority': 'low',
                'status': 'todo',
                'estimated_hours': 6,
                'tags': 'marketing,email'
            }
        ]
        
        for task_data in sample_tasks:
            task, created = Task.objects.get_or_create(
                title=task_data['title'],
                project=task_data['project'],
                defaults={
                    'description': task_data['description'],
                    'assigned_to': task_data['assigned_to'],
                    'due_date': task_data['due_date'],
                    'priority': task_data['priority'],
                    'status': task_data['status'],
                    'estimated_hours': task_data['estimated_hours'],
                    'tags': task_data['tags'],
                    'created_by': users[0]  # admin user
                }
            )
            if created:
                self.stdout.write(f'Created task: {task.title}')