"""Models for the redFlag reports application."""

import os
import secrets
import string
import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

def generate_reference_id():
    """Generate a high-entropy, cryptographically secure incident reference ID."""
    year = timezone.now().year
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters: 0, O, I, 1
    clean_alphabet = ''.join(c for c in alphabet if c not in '0OI1')
    code = ''.join(secrets.choice(clean_alphabet) for _ in range(6))
    return f"RF-{year}-{code}"

def evidence_upload_to(instance, filename):
    """Store evidence in private, hashed path with sanitized extension."""
    ext = os.path.splitext(filename)[1].lower()
    random_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('evidence', str(timezone.now().year), f"{timezone.now().month:02d}", random_filename)


class Department(models.Model):
    """Nodal department or enforcement agency handling case dispatch."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, unique=True, db_index=True)
    jurisdiction = models.CharField(max_length=150, default='National / Municipal')
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    head_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_departments')
    description = models.TextField(blank=True)
    sla_hours = models.PositiveIntegerField(default=48, help_text="Target SLA in hours")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def active_cases_count(self):
        return self.department_cases.exclude(status__in=['resolved', 'closed']).count()

    @property
    def total_cases_count(self):
        return self.department_cases.count()


class Report(models.Model):
    """Central grievance and public abuse incident record."""

    CATEGORY_CHOICES = [
        ('child_abuse', 'Child Abuse & Endangerment'),
        ('domestic_violence', 'Domestic Violence'),
        ('sexual_harassment', 'Sexual Harassment & Assault'),
        ('drug_trafficking', 'Illicit Drug Trafficking'),
        ('corruption_bribery', 'Corruption, Bribery & Misuse of Power'),
        ('cyber_bullying', 'Cyber Harassment & Digital Crimes'),
        ('robbery_theft', 'Robbery, Extortion & Theft'),
        ('human_trafficking', 'Human Trafficking'),
        ('other', 'Other Public Safety Grievance'),
    ]

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('critical', 'Critical / Urgent Alert'),
    ]

    reference_id = models.CharField(
        max_length=32,
        unique=True,
        default=generate_reference_id,
        db_index=True,
        editable=False,
        help_text="Secure public tracking identifier"
    )
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        help_text="Owner user if authenticated when submitting"
    )
    title = models.CharField(max_length=150, help_text="Concise summary of the incident")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField(max_length=5000, help_text="Detailed factual account of the incident")
    incident_date = models.DateTimeField(help_text="When the incident occurred")
    address = models.CharField(max_length=255, help_text="Physical location or street address")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    is_anonymous = models.BooleanField(
        default=False,
        help_text="Whether complainant identity should be completely masked"
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases',
        help_text="Assigned departmental staff investigator"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_cases',
        help_text="Designated nodal response department"
    )
    is_escalated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Marked for high-level director review"
    )
    escalation_reason = models.TextField(blank=True)
    internal_flag = models.CharField(max_length=50, blank=True)
    resolution_summary = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='submitted',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['is_escalated', '-created_at']),
        ]

    def __str__(self):
        return f"{self.reference_id} - {self.title[:40]}"

    def clean(self):
        super().clean()
        if self.incident_date and self.incident_date > timezone.now():
            raise ValidationError({'incident_date': 'Incident date and time cannot be in the future.'})

    def get_status_badge_classes(self):
        """Tailwind class names for accessible badge styling."""
        mapping = {
            'submitted': 'bg-slate-100 text-slate-800 border-slate-300',
            'under_review': 'bg-amber-100 text-amber-900 border-amber-300',
            'investigating': 'bg-sky-100 text-sky-900 border-sky-300',
            'resolved': 'bg-emerald-100 text-emerald-900 border-emerald-300',
            'closed': 'bg-red-100 text-red-900 border-red-300',
        }
        return mapping.get(self.status, 'bg-slate-100 text-slate-800 border-slate-300')

    def get_priority_badge_classes(self):
        """Tailwind badge styling for priority levels."""
        mapping = {
            'critical': 'bg-red-100 text-red-900 border-red-300 font-bold',
            'high': 'bg-orange-100 text-orange-900 border-orange-300 font-semibold',
            'medium': 'bg-amber-100 text-amber-900 border-amber-300',
            'low': 'bg-slate-100 text-slate-800 border-slate-300',
        }
        return mapping.get(self.priority, 'bg-slate-100 text-slate-800 border-slate-300')

    def filer_display(self):
        """Human-readable display of who submitted this report."""
        if self.is_anonymous:
            return "Anonymous Whistleblower"
        if self.reporter:
            full_name = self.reporter.get_full_name()
            return full_name if full_name else self.reporter.username
        if self.contact_email:
            return self.contact_email
        if self.contact_phone:
            return self.contact_phone
        return "Unregistered Citizen"


class Evidence(models.Model):
    """Uploaded supporting media and verification files."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='evidence_files')
    file = models.FileField(upload_to=evidence_upload_to)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    is_official = models.BooleanField(default=False, help_text="Uploaded by departmental authority")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_evidence')
    description = models.CharField(max_length=255, blank=True)
    file_hash = models.CharField(max_length=64, blank=True, help_text="SHA-256 integrity checksum")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Evidence for {self.report.reference_id} ({self.original_filename})"

    def human_readable_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def is_image(self):
        return self.mime_type.startswith('image/')

    def is_video(self):
        return self.mime_type.startswith('video/')

    def is_pdf(self):
        return self.mime_type == 'application/pdf'


class ReportStatusHistory(models.Model):
    """Immutable log of state machine transitions."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Public or official rationale for transition")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.report.reference_id}: {self.previous_status} -> {self.new_status} at {self.timestamp}"


class AuditEvent(models.Model):
    """Security audit trail for sensitive departmental actions."""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit {self.action} on {self.resource_type}:{self.resource_id} by {self.user}"


class SystemAnnouncement(models.Model):
    """Public or staff-only safety notices and operational advisories."""

    URGENCY_CHOICES = [
        ('info', 'General Advisory'),
        ('warning', 'Public Warning / Alert'),
        ('critical', 'Emergency High Alert'),
    ]
    AUDIENCE_CHOICES = [
        ('all', 'Public & Staff'),
        ('staff_only', 'Staff & Investigators Only'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default='Public Safety Bulletin')
    content = models.TextField()
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='info')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all')
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.urgency.upper()}] {self.title}"
