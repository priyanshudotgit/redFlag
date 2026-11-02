"""Integration tests for redFlag public and reporting views."""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.reports.models import Report

class PublicAndReportingViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_public_pages_status_200(self):
        pages = ['home', 'how_it_works', 'helpline', 'transparency', 'privacy', 'terms', 'report_track']
        for page_name in pages:
            url = reverse(page_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Page {page_name} failed with {response.status_code}")

    def test_report_submission_post_and_redirect(self):
        past_date = (timezone.now() - timezone.timedelta(days=1)).date()
        past_time = timezone.now().time()
        payload = {
            'title': 'Illegal Sewage Dump at Pier 4',
            'category': 'other',
            'description': 'Witnessed direct pipe dumping into harbor waters.',
            'date': past_date,
            'time': past_time,
            'address': 'Pier 4 Harbor Basin',
            'is_anonymous': 'on',
        }
        response = self.client.post(reverse('report_submit'), data=payload)
        self.assertEqual(response.status_code, 302)

        # Confirm report saved to database
        report = Report.objects.filter(title='Illegal Sewage Dump at Pier 4').first()
        self.assertIsNotNone(report)
        self.assertEqual(report.status, 'submitted')
        self.assertTrue(report.is_anonymous)

        # Follow redirect to acknowledgement
        ack_url = reverse('report_acknowledgement', kwargs={'reference_id': report.reference_id})
        self.assertRedirects(response, ack_url)

        ack_response = self.client.get(ack_url)
        self.assertEqual(ack_response.status_code, 200)
        self.assertContains(ack_response, report.reference_id)

    def test_report_tracking_view(self):
        report = Report.objects.create(
            title="Noise Violation Factory",
            category="other",
            description="Loud machinery operating past statutory midnight curfew.",
            incident_date=timezone.now() - timezone.timedelta(days=1),
            address="Industrial Block C",
            status="investigating"
        )
        url = reverse('report_track') + f"?reference_id={report.reference_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, report.reference_id)
        self.assertContains(response, "Investigating")

    def test_report_tracking_invalid_id(self):
        url = reverse('report_track') + "?reference_id=RF-9999-NONEXIST"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No incident record found")

