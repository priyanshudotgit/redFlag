"""Comprehensive views for redFlag departmental admin platform, command center, and case workbench."""

import os
import csv
import json
import hashlib
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone

from apps.reports.models import Report, Evidence, ReportStatusHistory, AuditEvent, Department, SystemAnnouncement
from apps.reviews.models import ReviewNote, InvestigationTask
from apps.accounts.models import ReporterProfile
from apps.reviews.forms import (
    StatusTransitionForm, CaseAssignmentForm, CasePriorityForm,
    OfficialEvidenceUploadForm, InvestigationTaskForm, ReviewNoteForm,
    DepartmentForm, ReporterTrustForm, SystemAnnouncementForm
)

def staff_required(view_func):
    """Ensure user is logged in and possesses staff permissions."""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='login'
    )
    return actual_decorator(view_func)


# ==============================================================================
# 1. Executive Admin Command Center Dashboard
# ==============================================================================

@staff_required
def admin_command_center(request):
    """Central administrative command center displaying high-level intelligence and alerts."""
    total_cases = Report.objects.count()
    submitted_cases = Report.objects.filter(status='submitted').count()
    review_cases = Report.objects.filter(status='under_review').count()
    investigating_cases = Report.objects.filter(status='investigating').count()
    resolved_cases = Report.objects.filter(status='resolved').count()
    closed_cases = Report.objects.filter(status='closed').count()

    critical_cases_count = Report.objects.filter(priority='critical').exclude(status__in=['resolved', 'closed']).count()
    escalated_cases_count = Report.objects.filter(is_escalated=True).exclude(status__in=['resolved', 'closed']).count()

    resolution_rate = round((resolved_cases / total_cases * 100), 1) if total_cases > 0 else 0.0

    # Urgent cases requiring prompt departmental attention
    urgent_cases = Report.objects.filter(
        Q(priority='critical') | Q(is_escalated=True)
    ).exclude(status__in=['resolved', 'closed']).order_by('-created_at')[:6]

    # Category distribution
    category_counts = Report.objects.values('category').annotate(count=Count('id')).order_by('-count')
    category_dict = dict(Report.CATEGORY_CHOICES)

    # Department caseloads
    departments = Department.objects.filter(is_active=True).annotate(
        active_count=Count('department_cases', filter=~Q(department_cases__status__in=['resolved', 'closed']))
    ).order_by('-active_count')[:6]

    # Recent Audit Log Activity
    recent_audits = AuditEvent.objects.all().order_by('-timestamp')[:8]

    # Recent Status Transitions
    recent_transitions = ReportStatusHistory.objects.select_related('report', 'changed_by').order_by('-timestamp')[:6]

    # Active system announcements
    announcements = SystemAnnouncement.objects.filter(is_active=True).order_by('-created_at')[:3]

    metrics = {
        'total': total_cases,
        'submitted': submitted_cases,
        'under_review': review_cases,
        'investigating': investigating_cases,
        'resolved': resolved_cases,
        'closed': closed_cases,
        'critical': critical_cases_count,
        'escalated': escalated_cases_count,
        'resolution_rate': resolution_rate,
        'total_evidence': Evidence.objects.count(),
        'total_departments': Department.objects.filter(is_active=True).count(),
        'total_officers': User.objects.filter(is_staff=True).count(),
        'total_citizens': User.objects.filter(is_staff=False).count(),
    }

    return render(request, 'reviews/command_center.html', {
        'metrics': metrics,
        'urgent_cases': urgent_cases,
        'category_counts': category_counts,
        'category_dict': category_dict,
        'departments': departments,
        'recent_audits': recent_audits,
        'recent_transitions': recent_transitions,
        'announcements': announcements,
    })


# ==============================================================================
# 2. Advanced Cases Management & Triage Backlog
# ==============================================================================

@staff_required
def staff_queue(request):
    """Case triage queue with extensive multi-criteria filtering and bulk action capabilities."""
    reports_qs = Report.objects.select_related('reporter', 'assigned_to', 'department').prefetch_related('evidence_files').order_by('-created_at')

    # Bulk action handling
    if request.method == 'POST' and 'bulk_action' in request.POST:
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.getlist('selected_cases')
        if selected_ids:
            target_reports = Report.objects.filter(id__in=selected_ids)
            count = target_reports.count()

            if action == 'mark_under_review':
                for r in target_reports:
                    if r.status == 'submitted':
                        r.status = 'under_review'
                        r.save()
                        ReportStatusHistory.objects.create(
                            report=r, previous_status='submitted', new_status='under_review',
                            changed_by=request.user, notes='Batch intake update to Under Review.'
                        )
                messages.success(request, f"Updated {count} case(s) to Under Review.")

            elif action == 'mark_investigating':
                for r in target_reports:
                    if r.status in ['submitted', 'under_review']:
                        prev = r.status
                        r.status = 'investigating'
                        r.save()
                        ReportStatusHistory.objects.create(
                            report=r, previous_status=prev, new_status='investigating',
                            changed_by=request.user, notes='Batch dispatch to formal investigation.'
                        )
                messages.success(request, f"Advanced {count} case(s) to Investigating.")

            elif action == 'set_critical':
                target_reports.update(priority='critical', is_escalated=True)
                messages.success(request, f"Flagged {count} case(s) as Critical Priority & Escalated.")

            elif action == 'export_selected':
                return export_cases_to_csv(target_reports)

            AuditEvent.objects.create(
                user=request.user,
                action='BULK_CASE_ACTION',
                resource_type='Report',
                resource_id=f"{count}_cases",
                details=f"Bulk action '{action}' performed on IDs: {selected_ids}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('staff_queue')

    # Filters
    query = request.GET.get('q', '').strip()
    if query:
        reports_qs = reports_qs.filter(
            Q(reference_id__icontains=query) |
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query) |
            Q(reporter__username__icontains=query) |
            Q(reporter__first_name__icontains=query) |
            Q(reporter__last_name__icontains=query) |
            Q(contact_email__icontains=query) |
            Q(contact_phone__icontains=query)
        )

    selected_category = request.GET.get('category', '')
    if selected_category:
        reports_qs = reports_qs.filter(category=selected_category)

    selected_status = request.GET.get('status', '')
    if selected_status:
        reports_qs = reports_qs.filter(status=selected_status)

    selected_priority = request.GET.get('priority', '')
    if selected_priority:
        reports_qs = reports_qs.filter(priority=selected_priority)

    filing_type = request.GET.get('filing_type', '')
    if filing_type == 'anonymous':
        reports_qs = reports_qs.filter(is_anonymous=True)
    elif filing_type == 'identified':
        reports_qs = reports_qs.filter(is_anonymous=False)

    department_id = request.GET.get('department', '')
    if department_id:
        reports_qs = reports_qs.filter(department_id=department_id)

    assigned_filter = request.GET.get('assigned_to', '')
    if assigned_filter == 'unassigned':
        reports_qs = reports_qs.filter(assigned_to__isnull=True)
    elif assigned_filter == 'me':
        reports_qs = reports_qs.filter(assigned_to=request.user)
    elif assigned_filter.isdigit():
        reports_qs = reports_qs.filter(assigned_to_id=int(assigned_filter))

    escalated_only = request.GET.get('escalated', '')
    if escalated_only == '1':
        reports_qs = reports_qs.filter(is_escalated=True)

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        reports_qs = reports_qs.order_by('created_at')
    elif sort_by == 'priority':
        priority_order = {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}
        reports_qs = sorted(reports_qs, key=lambda r: priority_order.get(r.priority, 5))
    else:
        reports_qs = reports_qs.order_by('-created_at')

    # Quick metrics for badges
    metrics = {
        'total': Report.objects.count(),
        'submitted': Report.objects.filter(status='submitted').count(),
        'under_review': Report.objects.filter(status='under_review').count(),
        'investigating': Report.objects.filter(status='investigating').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
        'closed': Report.objects.filter(status='closed').count(),
        'critical': Report.objects.filter(priority='critical').exclude(status__in=['resolved', 'closed']).count(),
        'escalated': Report.objects.filter(is_escalated=True).exclude(status__in=['resolved', 'closed']).count(),
    }

    paginator = Paginator(reports_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments_list = Department.objects.filter(is_active=True).order_by('name')
    officers_list = User.objects.filter(is_staff=True).order_by('first_name', 'username')

    return render(request, 'reviews/queue.html', {
        'page_obj': page_obj,
        'metrics': metrics,
        'categories': Report.CATEGORY_CHOICES,
        'statuses': Report.STATUS_CHOICES,
        'priorities': Report.PRIORITY_CHOICES,
        'departments': departments_list,
        'officers': officers_list,
        'selected_category': selected_category,
        'selected_status': selected_status,
        'selected_priority': selected_priority,
        'selected_department': department_id,
        'selected_assigned': assigned_filter,
        'filing_type': filing_type,
        'escalated_only': escalated_only,
        'sort_by': sort_by,
        'query': query,
    })


# ==============================================================================
# 3. Case Detail & Full Investigation Workbench
# ==============================================================================

@staff_required
def staff_report_detail(request, pk):
    """Complete investigation workbench with dossier, priority control, assignment, and tasks."""
    report = get_object_or_404(
        Report.objects.select_related('reporter', 'assigned_to', 'department'),
        pk=pk
    )
    evidence_files = report.evidence_files.select_related('uploaded_by').order_by('uploaded_at')
    status_history = report.status_history.select_related('changed_by').order_by('timestamp')
    internal_notes = report.internal_notes.select_related('author').order_by('-is_pinned', '-created_at')
    tasks = report.tasks.select_related('assigned_to', 'completed_by').order_by('is_completed', 'created_at')

    # Associated reporter track record
    reporter_profile = None
    reporter_other_reports = []
    if report.reporter:
        reporter_profile = getattr(report.reporter, 'profile', None)
        reporter_other_reports = report.reporter.reports.exclude(pk=report.pk).order_by('-created_at')[:4]

    # Forms
    status_form = StatusTransitionForm(current_status=report.status)
    assignment_form = CaseAssignmentForm(initial={
        'assigned_to': report.assigned_to,
        'department': report.department
    })
    priority_form = CasePriorityForm(initial={
        'priority': report.priority,
        'is_escalated': report.is_escalated,
        'escalation_reason': report.escalation_reason
    })
    note_form = ReviewNoteForm()
    task_form = InvestigationTaskForm()
    evidence_upload_form = OfficialEvidenceUploadForm()

    return render(request, 'reviews/detail.html', {
        'report': report,
        'evidence_files': evidence_files,
        'status_history': status_history,
        'internal_notes': internal_notes,
        'tasks': tasks,
        'reporter_profile': reporter_profile,
        'reporter_other_reports': reporter_other_reports,
        'status_form': status_form,
        'assignment_form': assignment_form,
        'priority_form': priority_form,
        'note_form': note_form,
        'task_form': task_form,
        'evidence_upload_form': evidence_upload_form,
    })


@staff_required
def printable_case_dossier(request, pk):
    """Printable official case dossier formatted for physical archives or court transmission."""
    report = get_object_or_404(Report.objects.select_related('reporter', 'assigned_to', 'department'), pk=pk)
    evidence_files = report.evidence_files.all()
    status_history = report.status_history.select_related('changed_by').order_by('timestamp')
    tasks = report.tasks.all()

    AuditEvent.objects.create(
        user=request.user,
        action='PRINT_CASE_DOSSIER',
        resource_type='Report',
        resource_id=report.reference_id,
        details='Generated official printable case dossier',
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return render(request, 'reviews/case_dossier_print.html', {
        'report': report,
        'evidence_files': evidence_files,
        'status_history': status_history,
        'tasks': tasks,
        'now': timezone.now(),
    })


# ==============================================================================
# 4. Status, Assignment, and Priority Handlers
# ==============================================================================

@staff_required
def update_status(request, pk):
    """Execute validated status change with notes and resolution summary."""
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = StatusTransitionForm(request.POST, current_status=report.status)
        if form.is_valid():
            new_status = form.cleaned_data['new_status']
            notes = form.cleaned_data['notes']
            resolution_summary = form.cleaned_data.get('resolution_summary', '')
            prev_status = report.status

            with transaction.atomic():
                report.status = new_status
                if resolution_summary:
                    report.resolution_summary = resolution_summary
                report.save()

                ReportStatusHistory.objects.create(
                    report=report,
                    previous_status=prev_status,
                    new_status=new_status,
                    changed_by=request.user,
                    notes=notes or f"Status transitioned from {prev_status} to {new_status}."
                )

                AuditEvent.objects.create(
                    user=request.user,
                    action='STATUS_TRANSITION',
                    resource_type='Report',
                    resource_id=report.reference_id,
                    details=f"From: {prev_status} -> To: {new_status}. Notes: {notes}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

            messages.success(request, f"Case {report.reference_id} status updated to '{report.get_status_display()}'.")
        else:
            messages.error(request, "Failed to update status. Please check permitted transitions.")
    return redirect('staff_report_detail', pk=pk)


@staff_required
def assign_case(request, pk):
    """Assign case to investigating staff officer and nodal department."""
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = CaseAssignmentForm(request.POST)
        if form.is_valid():
            assigned_to = form.cleaned_data['assigned_to']
            department = form.cleaned_data['department']
            dispatch_notes = form.cleaned_data.get('dispatch_notes', '')

            with transaction.atomic():
                report.assigned_to = assigned_to
                report.department = department
                report.save()

                # Record in status history if dispatched
                log_text = f"Assigned to {assigned_to.username if assigned_to else 'Unassigned'}. "
                if department:
                    log_text += f"Dispatched to {department.name}. "
                if dispatch_notes:
                    log_text += f"Note: {dispatch_notes}"

                ReportStatusHistory.objects.create(
                    report=report,
                    previous_status=report.status,
                    new_status=report.status,
                    changed_by=request.user,
                    notes=log_text
                )

                AuditEvent.objects.create(
                    user=request.user,
                    action='CASE_ASSIGNMENT_CHANGED',
                    resource_type='Report',
                    resource_id=report.reference_id,
                    details=log_text,
                    ip_address=request.META.get('REMOTE_ADDR')
                )

            messages.success(request, f"Case {report.reference_id} assignment successfully updated.")
        else:
            messages.error(request, "Failed to update assignment.")
    return redirect('staff_report_detail', pk=pk)


@staff_required
def update_priority(request, pk):
    """Update priority severity and toggle high-level director escalation."""
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = CasePriorityForm(request.POST)
        if form.is_valid():
            report.priority = form.cleaned_data['priority']
            report.is_escalated = form.cleaned_data['is_escalated']
            report.escalation_reason = form.cleaned_data.get('escalation_reason', '')
            report.save()

            AuditEvent.objects.create(
                user=request.user,
                action='PRIORITY_UPDATED',
                resource_type='Report',
                resource_id=report.reference_id,
                details=f"Priority: {report.priority}, Escalated: {report.is_escalated}, Reason: {report.escalation_reason}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Priority level for {report.reference_id} updated to {report.get_priority_display()}.")
    return redirect('staff_report_detail', pk=pk)


# ==============================================================================
# 5. Evidence & Investigation Task Management
# ==============================================================================

@staff_required
def upload_official_evidence(request, pk):
    """Authorized departmental staff uploading official forensic / FIR evidence."""
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = OfficialEvidenceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['evidence_file']
            desc = form.cleaned_data['description']

            # Compute SHA-256
            sha = hashlib.sha256()
            for chunk in uploaded_file.chunks():
                sha.update(chunk)
            checksum = sha.hexdigest()

            evidence = Evidence.objects.create(
                report=report,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=getattr(uploaded_file, 'content_type', 'application/octet-stream'),
                is_official=True,
                uploaded_by=request.user,
                description=desc,
                file_hash=checksum
            )

            AuditEvent.objects.create(
                user=request.user,
                action='OFFICIAL_EVIDENCE_ATTACHED',
                resource_type='Evidence',
                resource_id=str(evidence.pk),
                details=f"Attached official evidence '{desc}' to case {report.reference_id} (SHA256: {checksum[:12]}...)",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Official evidence '{desc}' attached with checksum verified.")
        else:
            messages.error(request, "Failed to upload official evidence. Check file type and size.")
    return redirect('staff_report_detail', pk=pk)


@staff_required
def add_investigation_task(request, pk):
    """Add a checklist task to the investigation."""
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = InvestigationTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.report = report
            task.save()
            messages.success(request, f"Task '{task.title}' added to investigation checklist.")
        else:
            messages.error(request, "Please enter a valid task title.")
    return redirect('staff_report_detail', pk=pk)


@staff_required
def toggle_investigation_task(request, pk, task_id):
    """Toggle completion status of an investigation task."""
    report = get_object_or_404(Report, pk=pk)
    task = get_object_or_404(InvestigationTask, pk=task_id, report=report)

    task.is_completed = not task.is_completed
    if task.is_completed:
        task.completed_by = request.user
        task.completed_at = timezone.now()
    else:
        task.completed_by = None
        task.completed_at = None
    task.save()

    AuditEvent.objects.create(
        user=request.user,
        action='INVESTIGATION_TASK_TOGGLED',
        resource_type='InvestigationTask',
        resource_id=str(task.pk),
        details=f"Task '{task.title}' marked as {'completed' if task.is_completed else 'pending'}",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    messages.info(request, f"Task '{task.title}' marked as {'completed' if task.is_completed else 'pending'}.")
    return redirect('staff_report_detail', pk=pk)


@staff_required
def add_review_note(request, pk):
    """Add a confidential staff-only investigation note."""
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        form = ReviewNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.report = report
            note.author = request.user
            note.save()

            AuditEvent.objects.create(
                user=request.user,
                action='INTERNAL_NOTE_ADDED',
                resource_type='Report',
                resource_id=report.reference_id,
                details=f"Note ID {note.pk} appended by {request.user.username} (Urgency: {note.urgency})",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, "Internal case note recorded.")
        else:
            messages.error(request, "Note content cannot be empty.")
    return redirect('staff_report_detail', pk=pk)


@staff_required
def download_evidence(request, pk):
    """Authorized streaming download of uploaded evidence file with audit log."""
    evidence = get_object_or_404(Evidence, pk=pk)
    if not evidence.file or not os.path.exists(evidence.file.path):
        raise Http404("Evidence file not found on disk.")

    AuditEvent.objects.create(
        user=request.user,
        action='EVIDENCE_DOWNLOADED',
        resource_type='Evidence',
        resource_id=str(evidence.pk),
        details=f"Downloaded '{evidence.original_filename}' associated with case {evidence.report.reference_id}",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    response = FileResponse(
        open(evidence.file.path, 'rb'),
        as_attachment=True,
        filename=evidence.original_filename
    )
    response['Content-Type'] = evidence.mime_type or 'application/octet-stream'
    return response


# ==============================================================================
# 6. Nodal Departments & Agencies Management
# ==============================================================================

@staff_required
def department_list(request):
    """List and manage nodal response departments."""
    departments = Department.objects.annotate(
        active_cases=Count('department_cases', filter=~Q(department_cases__status__in=['resolved', 'closed'])),
        total_cases=Count('department_cases')
    ).order_by('name')

    form = DepartmentForm()
    return render(request, 'reviews/departments.html', {
        'departments': departments,
        'form': form,
    })


@staff_required
def department_create(request):
    """Create a new nodal agency or response department."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            AuditEvent.objects.create(
                user=request.user,
                action='DEPARTMENT_CREATED',
                resource_type='Department',
                resource_id=dept.code,
                details=f"Created department '{dept.name}'",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Department '{dept.name}' registered successfully.")
        else:
            messages.error(request, "Please correct errors in the department form.")
    return redirect('department_list')


# ==============================================================================
# 7. Citizen Reporters Directory & Trust Verification
# ==============================================================================

@staff_required
def reporter_list(request):
    """Manage registered citizen reporters, view credibility, and flag fraudulent filers."""
    reporters = User.objects.filter(is_staff=False).select_related('profile').annotate(
        total_filings=Count('reports'),
        resolved_filings=Count('reports', filter=Q(reports__status='resolved'))
    ).order_by('-date_joined')

    search_query = request.GET.get('q', '').strip()
    if search_query:
        reporters = reporters.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    paginator = Paginator(reporters, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reviews/reporters.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


@staff_required
def reporter_detail(request, pk):
    """Detailed citizen profile, past filings history, and trust status verification."""
    citizen = get_object_or_404(User.objects.filter(is_staff=False).select_related('profile'), pk=pk)
    citizen_reports = citizen.reports.order_by('-created_at')

    profile = getattr(citizen, 'profile', None)
    if not profile:
        profile = ReporterProfile.objects.create(user=citizen)

    if request.method == 'POST':
        form = ReporterTrustForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            AuditEvent.objects.create(
                user=request.user,
                action='REPORTER_TRUST_UPDATED',
                resource_type='User',
                resource_id=str(citizen.pk),
                details=f"Trust status for {citizen.username} set to '{profile.trust_status}'",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Trust verification status for {citizen.username} updated.")
            return redirect('reporter_detail', pk=pk)
    else:
        form = ReporterTrustForm(instance=profile)

    return render(request, 'reviews/reporter_detail.html', {
        'citizen': citizen,
        'profile': profile,
        'reports': citizen_reports,
        'form': form,
    })


# ==============================================================================
# 8. Staff Officers & Team Caseload Directory
# ==============================================================================

@staff_required
def officer_list(request):
    """Directory of all investigating staff officers, designations, and active assignments."""
    officers = User.objects.filter(is_staff=True).annotate(
        active_cases_count=Count('assigned_cases', filter=~Q(assigned_cases__status__in=['resolved', 'closed'])),
        total_cases_count=Count('assigned_cases')
    ).order_by('first_name', 'username')

    return render(request, 'reviews/officers.html', {
        'officers': officers,
    })


# ==============================================================================
# 9. System Security Audit Trail & Activity Logs
# ==============================================================================

@staff_required
def audit_log_list(request):
    """Searchable system security audit trail recording all administrative actions."""
    logs_qs = AuditEvent.objects.select_related('user').order_by('-timestamp')

    action_filter = request.GET.get('action', '')
    if action_filter:
        logs_qs = logs_qs.filter(action=action_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        logs_qs = logs_qs.filter(
            Q(resource_id__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )

    # Distinct actions for filter dropdown
    distinct_actions = AuditEvent.objects.values_list('action', flat=True).distinct().order_by('action')

    paginator = Paginator(logs_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'reviews/audit_logs.html', {
        'page_obj': page_obj,
        'distinct_actions': distinct_actions,
        'selected_action': action_filter,
        'search_query': search_query,
    })


# ==============================================================================
# 10. Intelligence & Data Export Hub
# ==============================================================================

def export_cases_to_csv(queryset):
    """Stream CSV file containing case ledger for departmental reporting."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="redflag_cases_export_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Reference ID', 'Title', 'Category', 'Priority', 'Status', 'Is Escalated',
        'Filer Type', 'Reporter Username', 'Contact Email', 'Contact Phone',
        'Occurrence Date', 'Address', 'Latitude', 'Longitude',
        'Assigned Department', 'Assigned Officer', 'Date Filed', 'Resolution Summary'
    ])

    for r in queryset:
        writer.writerow([
            r.reference_id,
            r.title,
            r.get_category_display(),
            r.get_priority_display(),
            r.get_status_display(),
            'YES' if r.is_escalated else 'NO',
            'Anonymous' if r.is_anonymous else 'Identified',
            r.reporter.username if r.reporter else '',
            r.contact_email,
            r.contact_phone,
            r.incident_date.strftime('%Y-%m-%d %H:%M:%S') if r.incident_date else '',
            r.address,
            r.latitude or '',
            r.longitude or '',
            r.department.name if r.department else 'Unassigned',
            r.assigned_to.username if r.assigned_to else 'Unassigned',
            r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            r.resolution_summary
        ])

    return response


@staff_required
def export_hub(request):
    """Intelligence and export center to download custom CSV and JSON datasets."""
    if request.method == 'POST':
        status_filter = request.POST.get('status', '')
        category_filter = request.POST.get('category', '')
        priority_filter = request.POST.get('priority', '')
        format_type = request.POST.get('format', 'csv')

        qs = Report.objects.all().order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(category=category_filter)
        if priority_filter:
            qs = qs.filter(priority=priority_filter)

        AuditEvent.objects.create(
            user=request.user,
            action='DATA_EXPORT_GENERATED',
            resource_type='Report',
            resource_id=f"{qs.count()}_cases",
            details=f"Exported format={format_type}, status={status_filter}, category={category_filter}, priority={priority_filter}",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        if format_type == 'json':
            data = []
            for r in qs:
                data.append({
                    'reference_id': r.reference_id,
                    'title': r.title,
                    'category': r.category,
                    'priority': r.priority,
                    'status': r.status,
                    'is_anonymous': r.is_anonymous,
                    'incident_date': r.incident_date.isoformat() if r.incident_date else None,
                    'address': r.address,
                    'department': r.department.name if r.department else None,
                    'assigned_to': r.assigned_to.username if r.assigned_to else None,
                    'created_at': r.created_at.isoformat(),
                    'resolution_summary': r.resolution_summary,
                })
            response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            response['Content-Disposition'] = f'attachment; filename="redflag_cases_{timestamp}.json"'
            return response
        else:
            return export_cases_to_csv(qs)

    return render(request, 'reviews/export_hub.html', {
        'categories': Report.CATEGORY_CHOICES,
        'statuses': Report.STATUS_CHOICES,
        'priorities': Report.PRIORITY_CHOICES,
        'total_cases': Report.objects.count(),
    })


# ==============================================================================
# 11. System Announcements & Safety Advisories
# ==============================================================================

@staff_required
def announcement_list(request):
    """Manage safety alerts and operational directives."""
    announcements = SystemAnnouncement.objects.select_related('created_by').order_by('-created_at')
    form = SystemAnnouncementForm()

    if request.method == 'POST':
        form = SystemAnnouncementForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()

            AuditEvent.objects.create(
                user=request.user,
                action='ANNOUNCEMENT_CREATED',
                resource_type='SystemAnnouncement',
                resource_id=str(item.pk),
                details=f"Created bulletin '{item.title}' (Urgency: {item.urgency})",
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Advisory '{item.title}' published.")
            return redirect('announcement_list')

    return render(request, 'reviews/announcements.html', {
        'announcements': announcements,
        'form': form,
    })


@staff_required
def announcement_toggle(request, pk):
    """Toggle active status of a bulletin."""
    announcement = get_object_or_404(SystemAnnouncement, pk=pk)
    announcement.is_active = not announcement.is_active
    announcement.save()
    messages.info(request, f"Advisory '{announcement.title}' is now {'active' if announcement.is_active else 'archived'}.")
    return redirect('announcement_list')
