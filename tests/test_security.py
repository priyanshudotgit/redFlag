"""Security and authorization boundary tests for redFlag."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from apps.reports.models import Report

class SecurityAndAuthorizationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Regular Citizen User A
        self.user_a = User.objects.create_user(username='citizen_a', password='Password123!')

        # Regular Citizen User B
        self.user_b = User.objects.create_user(username='citizen_b', password='Password123!')

        # Staff Officer User
        self.staff_user = User.objects.create_user(username='officer_test', password='Password123!', is_staff=True)

        # Report owned by User A
        self.report_a = Report.objects.create(
            title="Private Allegation Filed by User A",
            category="corruption_bribery",
            description="Confidential report containing allegations.",
            incident_date=timezone.now() - timezone.timedelta(days=1),
            address="Civic Center",
            reporter=self.user_a,
            is_anonymous=False,
            contact_email="citizen_a@example.org"
        )

    def test_user_can_access_own_report(self):
        self.client.login(username='citizen_a', password='Password123!')
        url = reverse('report_detail', kwargs={'reference_id': self.report_a.reference_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.report_a.title)

    def test_cross_user_access_denied_403(self):
        """User B must be strictly forbidden from accessing User A's private report."""
        self.client.login(username='citizen_b', password='Password123!')
        url = reverse('report_detail', kwargs={'reference_id': self.report_a.reference_id})
        response = self.client.get(url)
        # Should raise PermissionDenied -> HTTP 403
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_report_detail_redirects_to_login(self):
        url = reverse('report_detail', kwargs={'reference_id': self.report_a.reference_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_non_staff_cannot_access_review_queue(self):
        """Regular citizens attempting to access /staff/queue/ must be redirected or denied."""
        self.client.login(username='citizen_a', password='Password123!')
        response = self.client.get(reverse('staff_queue'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_staff_user_can_access_queue_and_all_reports(self):
        self.client.login(username='officer_test', password='Password123!')

        # Access review queue
        queue_res = self.client.get(reverse('staff_queue'))
        self.assertEqual(queue_res.status_code, 200)
        self.assertContains(queue_res, self.report_a.reference_id)

        # Access report detail
        detail_res = self.client.get(reverse('staff_report_detail', kwargs={'pk': self.report_a.pk}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, self.report_a.title)

    def test_anonymous_submission_strips_contact_details(self):
        """Ensure anonymous reports strip contact identifiers on the backend."""
        past_date = (timezone.now() - timezone.timedelta(days=1)).date()
        past_time = timezone.now().time()
        payload = {
            'title': 'Anonymous Report with Inadvertent Contact',
            'category': 'drug_trafficking',
            'description': 'Suspicious trade behind warehouse.',
            'date': past_date,
            'time': past_time,
            'address': 'Old Depot',
            'is_anonymous': 'on',
            'contact_email': 'leak@example.org',
            'contact_phone': '555-1234',
        }
        res = self.client.post(reverse('report_submit'), data=payload)
        self.assertEqual(res.status_code, 302)

        saved = Report.objects.filter(title='Anonymous Report with Inadvertent Contact').first()
        self.assertIsNotNone(saved)
        self.assertTrue(saved.is_anonymous)
        self.assertEqual(saved.contact_email, '')
        self.assertEqual(saved.contact_phone, '')

