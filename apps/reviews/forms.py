"""Forms for departmental staff, admin operations, status transitions, and investigation workbench."""

import os
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.reports.models import Report, Department, SystemAnnouncement, Evidence
from apps.reviews.models import ReviewNote, InvestigationTask
from apps.accounts.models import ReporterProfile

class StatusTransitionForm(forms.Form):
    """Staff form to execute validated state machine transitions with resolution notes."""

    new_status = forms.ChoiceField(
        choices=Report.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm bg-white'
        })
    )
    notes = forms.CharField(
        label="Milestone Progress / Public Tracking Note",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
            'placeholder': 'Explain rationale for status transition (visible on timeline)...'
        })
    )
    resolution_summary = forms.CharField(
        label="Official Resolution Findings (Optional)",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
            'placeholder': 'Formal concluding findings or referral notice (if concluding case)...'
        })
    )

    def __init__(self, *args, current_status='submitted', **kwargs):
        super().__init__(*args, **kwargs)
        self.current_status = current_status

        valid_transitions = {
            'submitted': ['under_review', 'closed'],
            'under_review': ['investigating', 'resolved', 'closed'],
            'investigating': ['resolved', 'closed'],
            'resolved': ['closed', 'investigating'],
            'closed': ['under_review'],
        }

        allowed_keys = valid_transitions.get(current_status, [])
        self.fields['new_status'].choices = [
            (k, v) for k, v in Report.STATUS_CHOICES if k in allowed_keys
        ]

    def clean_new_status(self):
        new_status = self.cleaned_data['new_status']
        if new_status == self.current_status:
            raise ValidationError("Please select a status different from the current status.")
        return new_status


class CaseAssignmentForm(forms.Form):
    """Assign case to investigating staff member and nodal department."""

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True).order_by('first_name', 'username'),
        required=False,
        empty_label="— Unassigned —",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="— General Intake Queue —",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900'
        })
    )
    dispatch_notes = forms.CharField(
        label="Routing / Dispatch Instruction Note",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900',
            'placeholder': 'e.g. Priority dispatch for forensic review'
        })
    )


class CasePriorityForm(forms.Form):
    """Set priority level and manage director escalation."""

    priority = forms.ChoiceField(
        choices=Report.PRIORITY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-900'
        })
    )
    is_escalated = forms.BooleanField(
        label="Flag for High-Level Director Escalation",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-red-600 focus:ring-slate-900 border-slate-300 rounded'
        })
    )
    escalation_reason = forms.CharField(
        label="Escalation Rationale",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-slate-900',
            'placeholder': 'Reason for urgent escalation (e.g. ongoing threat, public health danger)'
        })
    )


class OfficialEvidenceUploadForm(forms.Form):
    """Upload official investigation documents, police reports, or forensic attachments."""

    evidence_file = forms.FileField(
        label="Official Document / File",
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-900 file:text-white hover:file:bg-slate-800 cursor-pointer',
            'accept': '.jpg,.jpeg,.png,.webp,.pdf,.mp4'
        })
    )
    description = forms.CharField(
        label="Document Title / Citation",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-1.5 border border-slate-300 rounded-md text-xs focus:outline-none focus:ring-2 focus:ring-slate-900',
            'placeholder': 'e.g. Police Station FIR #829 or Forensic Water Sample Report'
        })
    )

    def clean_evidence_file(self):
        f = self.cleaned_data['evidence_file']
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
        if f.size > max_size:
            raise ValidationError(f"File size ({f.size / (1024*1024):.1f}MB) exceeds 5MB limit.")
        ext = os.path.splitext(f.name)[1].lower()
        allowed = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp', '.pdf', '.mp4'])
        if ext not in allowed:
            raise ValidationError(f"Extension '{ext}' not allowed. Allowed: {', '.join(allowed)}")
        return f


class InvestigationTaskForm(forms.ModelForm):
    """Add actionable checklist task to a case."""

    class Meta:
        model = InvestigationTask
        fields = ['title', 'assigned_to', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-1.5 border border-slate-300 rounded-md text-xs focus:outline-none focus:ring-2 focus:ring-slate-900',
                'placeholder': 'e.g. Interview witness or inspect water valve'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full px-3 py-1.5 border border-slate-300 rounded-md text-xs bg-white focus:outline-none focus:ring-2 focus:ring-slate-900'
            }),
            'due_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-1.5 border border-slate-300 rounded-md text-xs focus:outline-none focus:ring-2 focus:ring-slate-900'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        self.fields['assigned_to'].empty_label = "— Assign to officer —"


class ReviewNoteForm(forms.ModelForm):
    """Confidential internal note with urgency tag."""

    class Meta:
        model = ReviewNote
        fields = ['content', 'urgency', 'is_pinned']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
                'placeholder': 'Add internal departmental note (visible to staff only)...'
            }),
            'urgency': forms.Select(attrs={
                'class': 'px-2.5 py-1.5 border border-slate-300 rounded-md text-xs bg-white focus:outline-none focus:ring-2 focus:ring-slate-900'
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-slate-900 focus:ring-slate-900 border-slate-300 rounded'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['urgency'].required = False
        self.fields['is_pinned'].required = False


class DepartmentForm(forms.ModelForm):
    """Manage response departments and agencies."""

    class Meta:
        model = Department
        fields = ['name', 'code', 'jurisdiction', 'contact_email', 'contact_phone', 'head_officer', 'sla_hours', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm font-mono uppercase'}),
            'jurisdiction': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'contact_email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'contact_phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'head_officer': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white'}),
            'sla_hours': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-slate-900 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['jurisdiction'].required = False
        self.fields['head_officer'].queryset = User.objects.filter(is_staff=True)
        self.fields['head_officer'].empty_label = "— Select Department Head —"
        self.fields['head_officer'].required = False
        self.fields['contact_email'].required = False
        self.fields['contact_phone'].required = False
        self.fields['description'].required = False
        self.fields['is_active'].required = False


class ReporterTrustForm(forms.ModelForm):
    """Staff verification and reputation management for citizen reporters."""

    class Meta:
        model = ReporterProfile
        fields = ['trust_status', 'reputation_score', 'phone', 'address', 'verification_notes']
        widgets = {
            'trust_status': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white'}),
            'reputation_score': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'verification_notes': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm', 'placeholder': 'Investigation notes regarding reporter credibility...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reputation_score'].required = False
        self.fields['phone'].required = False
        self.fields['address'].required = False
        self.fields['verification_notes'].required = False


class SystemAnnouncementForm(forms.ModelForm):
    """Create or modify public bulletins and staff directives."""

    class Meta:
        model = SystemAnnouncement
        fields = ['title', 'urgency', 'content', 'category', 'audience', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'urgency': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'category': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm'}),
            'audience': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-md text-sm bg-white'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-slate-900 rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['audience'].required = False
        self.fields['is_active'].required = False
