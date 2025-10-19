from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Task views
    # path('test/', views.test_view, name='test'),  # Test view
    path('', views.task_board, name='task_board'),
    path('create/', views.create_task, name='create_task'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/update/', views.update_task, name='update_task'),
    path('<int:pk>/delete/', views.delete_task, name='delete_task'),
    # path('filter/', views.filter_tasks, name='filter_tasks'),    
    
    # Project views
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    
    # Comment and Attachment views
    path('<int:task_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:task_id>/attachment/', views.add_attachment, name='add_attachment'),
    
    # # AJAX views
    # path('api/update-status/', views.update_task_status, name='update_task_status'),
    # path('api/reorder-tasks/', views.reorder_tasks, name='reorder_tasks'),
]