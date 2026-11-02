"""Tests for staff reviews, state machine transitions, and internal notes."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from apps.reports.models import Report, ReportStatusHistory, Evidence
from apps.reviews.models import ReviewNote

class ReviewWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staff_officer', password='Password123!', is_staff=True)
        self.normal_user = User.objects.create_user(username='civilian', password='Password123!')

        self.report = Report.objects.create(
            title="Extortion Tip",
            category="corruption_bribery",
            description="Demanding kickback for vendor license renewal.",
            incident_date=timezone.now() - timezone.timedelta(days=2),
            address="Licensing Desk Room 102",
            status="submitted"
        )

    def test_staff_status_transition_valid(self):
        self.client.login(username='staff_officer', password='Password123!')
        url = reverse('update_status', kwargs={'pk': self.report.pk})

        # Advance submitted -> under_review
        response = self.client.post(url, data={
            'new_status': 'under_review',
            'notes': 'Case assigned to Detective Jones for intake verification.'
        })
        self.assertEqual(response.status_code, 302)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'under_review')

        # Check status history
        hist = self.report.status_history.last()
        self.assertEqual(hist.previous_status, 'submitted')
        self.assertEqual(hist.new_status, 'under_review')
        self.assertIn('Detective Jones', hist.notes)

    def test_staff_add_confidential_note(self):
        self.client.login(username='staff_officer', password='Password123!')
        url = reverse('add_review_note', kwargs={'pk': self.report.pk})

        response = self.client.post(url, data={
            'content': 'Confidential tip: Informant states cash exchange occurred at lunch hour.'
        })
        self.assertEqual(response.status_code, 302)

        note = ReviewNote.objects.filter(report=self.report).first()
        self.assertIsNotNone(note)
        self.assertEqual(note.author, self.staff_user)
        self.assertIn('lunch hour', note.content)

    def test_non_staff_cannot_transition_status(self):
        self.client.login(username='civilian', password='Password123!')
        url = reverse('update_status', kwargs={'pk': self.report.pk})

        response = self.client.post(url, data={'new_status': 'resolved'})
        # Should redirect to login because not staff
        self.assertEqual(response.status_code, 302)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'submitted') # Unchanged

