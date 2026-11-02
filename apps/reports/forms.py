"""Forms for report submission and reference code tracking."""

import os
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.reports.models import Report

class ReportSubmissionForm(forms.ModelForm):
    """Incident report filing form with strict validation and optional evidence upload."""

    # Separate date and time fields for robust HTML5 native controls
    date = forms.DateField(
        label="Date of Incident",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm'
        })
    )
    time = forms.TimeField(
        label="Time of Incident",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm'
        })
    )
    evidence_file = forms.FileField(
        label="Supporting Evidence (Optional)",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-slate-900 file:text-white hover:file:bg-slate-800 cursor-pointer',
            'accept': '.jpg,.jpeg,.png,.webp,.pdf,.mp4'
        }),
        help_text="Max 5MB. Permitted types: JPG, PNG, WEBP, PDF, MP4."
    )

    class Meta:
        model = Report
        fields = [
            'title',
            'category',
            'description',
            'address',
            'latitude',
            'longitude',
            'is_anonymous',
            'contact_email',
            'contact_phone'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
                'placeholder': 'Concise title of the incident'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm bg-white'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
                'placeholder': 'Provide factual, chronological details of what occurred...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
                'placeholder': 'Street address, landmark, or intersection'
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-red-600 focus:ring-slate-900 border-slate-300 rounded'
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
                'placeholder': 'email@example.org'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-sm',
                'placeholder': '+1 (555) 000-0000'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if date and time:
            combined = timezone.datetime.combine(date, time)
            # Make timezone-aware
            tz = timezone.get_current_timezone()
            incident_dt = timezone.make_aware(combined, tz) if timezone.is_naive(combined) else combined

            if incident_dt > timezone.now():
                self.add_error('date', "Incident date and time cannot be in the future.")
            else:
                cleaned_data['incident_date'] = incident_dt

        # Evidence validation
        evidence = cleaned_data.get('evidence_file')
        if evidence:
            max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)
            if evidence.size > max_size:
                self.add_error('evidence_file', f"File size ({evidence.size / (1024*1024):.1f}MB) exceeds the 5MB limit.")

            ext = os.path.splitext(evidence.name)[1].lower()
            allowed_exts = getattr(settings, 'ALLOWED_UPLOAD_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.webp', '.pdf', '.mp4'])
            if ext not in allowed_exts:
                self.add_error('evidence_file', f"File extension '{ext}' is not permitted. Permitted: {', '.join(allowed_exts)}")

            allowed_mimes = getattr(settings, 'ALLOWED_MIME_TYPES', [
                'image/jpeg', 'image/png', 'image/webp', 'application/pdf', 'video/mp4'
            ])
            if hasattr(evidence, 'content_type') and evidence.content_type not in allowed_mimes:
                self.add_error('evidence_file', f"MIME type '{evidence.content_type}' is not recognized as safe media.")

        return cleaned_data


class ReportTrackForm(forms.Form):
    """Simple reference lookup form."""

    reference_id = forms.CharField(
        label="Incident Reference ID",
        max_length=40,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border-2 border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 text-center font-mono text-lg uppercase tracking-wider',
            'placeholder': 'e.g. RF-2026-9K8M2T',
            'autocomplete': 'off',
            'required': True
        })
    )

    def clean_reference_id(self):
        return self.cleaned_data['reference_id'].strip().upper()

