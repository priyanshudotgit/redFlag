"""URL configuration for reviews and administrative command center."""

from django.urls import path
from apps.reviews import views

urlpatterns = [
    # Command Center & Overview
    path('', views.admin_command_center, name='admin_command_center'),
    path('dashboard/', views.admin_command_center, name='admin_dashboard'),

    # Cases & Triage Queue
    path('queue/', views.staff_queue, name='staff_queue'),
    path('cases/', views.staff_queue, name='staff_cases'),
    path('reports/<int:pk>/', views.staff_report_detail, name='staff_report_detail'),
    path('reports/<int:pk>/dossier/', views.printable_case_dossier, name='printable_case_dossier'),

    # Case Actions
    path('reports/<int:pk>/status/', views.update_status, name='update_status'),
    path('reports/<int:pk>/assign/', views.assign_case, name='assign_case'),
    path('reports/<int:pk>/priority/', views.update_priority, name='update_priority'),
    path('reports/<int:pk>/evidence/upload/', views.upload_official_evidence, name='upload_official_evidence'),
    path('reports/<int:pk>/tasks/add/', views.add_investigation_task, name='add_investigation_task'),
    path('reports/<int:pk>/tasks/<int:task_id>/toggle/', views.toggle_investigation_task, name='toggle_investigation_task'),
    path('reports/<int:pk>/notes/', views.add_review_note, name='add_review_note'),
    path('evidence/<int:pk>/download/', views.download_evidence, name='download_evidence'),

    # Department & Agency Management
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),

    # Citizen Reporter Management & Verification
    path('reporters/', views.reporter_list, name='reporter_list'),
    path('reporters/<int:pk>/', views.reporter_detail, name='reporter_detail'),

    # Staff & Officers Caseload Directory
    path('officers/', views.officer_list, name='officer_list'),

    # Audit & Compliance Logs
    path('audit-logs/', views.audit_log_list, name='audit_log_list'),

    # Intelligence & Export Hub
    path('export/', views.export_hub, name='export_hub'),

    # Bulletins & Announcements
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/<int:pk>/toggle/', views.announcement_toggle, name='announcement_toggle'),
]
