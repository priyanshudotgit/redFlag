"""Views for report filing, acknowledgement, tracking, and detail inspection."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from apps.reports.models import Report, Evidence, ReportStatusHistory, AuditEvent
from apps.reports.forms import ReportSubmissionForm, ReportTrackForm

def submit_report(request):
    """File a new grievance or incident report with optional evidence."""
    if request.method == 'POST':
        form = ReportSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                report = form.save(commit=False)
                report.incident_date = form.cleaned_data['incident_date']

                if request.user.is_authenticated:
                    report.reporter = request.user

                # Ensure strict privacy if anonymous
                if report.is_anonymous:
                    report.contact_email = ''
                    report.contact_phone = ''

                report.save()

                # Process optional evidence upload
                evidence_file = form.cleaned_data.get('evidence_file')
                if evidence_file:
                    Evidence.objects.create(
                        report=report,
                        file=evidence_file,
                        original_filename=evidence_file.name,
                        file_size=evidence_file.size,
                        mime_type=getattr(evidence_file, 'content_type', 'application/octet-stream')
                    )

                # Create initial status history entry
                ReportStatusHistory.objects.create(
                    report=report,
                    previous_status='none',
                    new_status='submitted',
                    changed_by=request.user if request.user.is_authenticated else None,
                    notes='Incident report filed into national intake queue.'
                )

                # Record security audit event
                ip = request.META.get('REMOTE_ADDR')
                AuditEvent.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='REPORT_SUBMITTED',
                    resource_type='Report',
                    resource_id=report.reference_id,
                    details=f"Category: {report.category}, Anonymous: {report.is_anonymous}",
                    ip_address=ip
                )

            messages.success(request, "Incident report submitted successfully.")
            return redirect('report_acknowledgement', reference_id=report.reference_id)
        else:
            messages.error(request, "Please review and correct the errors indicated below.")
    else:
        form = ReportSubmissionForm()

    return render(request, 'reports/submit.html', {'form': form})


def report_acknowledgement(request, reference_id):
    """Receipt screen displaying official reference ID and tracking guidance."""
    report = get_object_or_404(Report, reference_id=reference_id)
    return render(request, 'reports/acknowledgement.html', {'report': report})


def track_report(request):
    """Public lookup for incident status using reference code without leaking private allegations."""
    form = ReportTrackForm(request.GET or None)
    report = None
    status_history = None

    if form.is_valid():
        reference_id = form.cleaned_data['reference_id']
        try:
            report = Report.objects.get(reference_id=reference_id)
            status_history = report.status_history.all().order_by('timestamp')
        except Report.DoesNotExist:
            messages.error(request, f"No incident record found matching reference code '{reference_id}'. Please verify and try again.")

    return render(request, 'reports/track.html', {
        'form': form,
        'report': report,
        'status_history': status_history,
    })


@login_required
def report_detail(request, reference_id):
    """Detailed case view strictly restricted to the owning reporter or staff."""
    report = get_object_or_404(Report, reference_id=reference_id)

    # Object-level permission check
    if report.reporter != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to view this report.")

    evidence_files = report.evidence_files.all()
    status_history = report.status_history.all().order_by('timestamp')

    return render(request, 'reports/detail.html', {
        'report': report,
        'evidence_files': evidence_files,
        'status_history': status_history,
    })

