"""Unit tests for redFlag forms and validation."""

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from apps.reports.forms import ReportSubmissionForm, ReportTrackForm
from apps.accounts.forms import UserRegistrationForm
from apps.reviews.forms import StatusTransitionForm

class FormValidationTests(TestCase):
    def test_valid_report_form(self):
        past_date = (timezone.now() - timezone.timedelta(days=1)).date()
        past_time = timezone.now().time()
        form_data = {
            'title': 'Stolen Bicycle from Park Railing',
            'category': 'robbery_theft',
            'description': 'Witnessed individual cutting lock on silver bicycle at main gate.',
            'date': past_date,
            'time': past_time,
            'address': 'Main Park West Gate',
            'is_anonymous': True,
        }
        form = ReportSubmissionForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn('incident_date', form.cleaned_data)

    def test_report_form_future_date_rejected(self):
        future_date = (timezone.now() + timezone.timedelta(days=2)).date()
        past_time = timezone.now().time()
        form_data = {
            'title': 'Future Incident',
            'category': 'other',
            'description': 'This should fail validation because date is in the future.',
            'date': future_date,
            'time': past_time,
            'address': 'City Hall',
        }
        form = ReportSubmissionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_evidence_file_extension_validation(self):
        past_date = (timezone.now() - timezone.timedelta(days=1)).date()
        past_time = timezone.now().time()
        form_data = {
            'title': 'Malicious Script Upload Attempt',
            'category': 'other',
            'description': 'Testing file extension allowlist rejection.',
            'date': past_date,
            'time': past_time,
            'address': 'Test Lab',
        }
        bad_file = SimpleUploadedFile("malicious.sh", b"#!/bin/bash\necho hack", content_type="application/x-sh")
        form = ReportSubmissionForm(data=form_data, files={'evidence_file': bad_file})
        self.assertFalse(form.is_valid())
        self.assertIn('evidence_file', form.errors)

    def test_evidence_file_size_validation(self):
        past_date = (timezone.now() - timezone.timedelta(days=1)).date()
        past_time = timezone.now().time()
        form_data = {
            'title': 'Huge File Upload Attempt',
            'category': 'other',
            'description': 'Testing file size limit rejection.',
            'date': past_date,
            'time': past_time,
            'address': 'Test Lab',
        }
        # 6MB dummy content
        big_file = SimpleUploadedFile("huge.jpg", b"x" * (6 * 1024 * 1024), content_type="image/jpeg")
        form = ReportSubmissionForm(data=form_data, files={'evidence_file': big_file})
        self.assertFalse(form.is_valid())
        self.assertIn('evidence_file', form.errors)

    def test_status_transition_form(self):
        # From 'submitted', allowed transitions are 'under_review' and 'closed'
        form = StatusTransitionForm(current_status='submitted')
        allowed_choices = [c[0] for c in form.fields['new_status'].choices]
        self.assertIn('under_review', allowed_choices)
        self.assertIn('closed', allowed_choices)
        self.assertNotIn('resolved', allowed_choices) # Cannot jump directly from submitted to resolved

    def test_user_registration_form(self):
        form_data = {
            'username': 'newcitizen',
            'email': 'citizen@example.org',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.check_password('Password123!'))

    def test_user_registration_mismatch_password(self):
        form_data = {
            'username': 'badcitizen',
            'email': 'bad@example.org',
            'password': 'Password123!',
            'password_confirm': 'DifferentPassword456!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)

