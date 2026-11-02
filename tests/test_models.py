"""Unit tests for redFlag data models."""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.reports.models import Report, Evidence, ReportStatusHistory, AuditEvent, generate_reference_id

class ReportModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testreporter', password='Password123!')

    def test_reference_id_generation(self):
        ref1 = generate_reference_id()
        ref2 = generate_reference_id()
        self.assertTrue(ref1.startswith('RF-'))
        self.assertNotEqual(ref1, ref2)
        self.assertEqual(len(ref1), 14) # RF-YYYY-XXXXXX = 3 + 4 + 1 + 6 = 14

    def test_report_creation(self):
        report = Report.objects.create(
            title="Illegal Dumping in Stream",
            category="other",
            description="Truck dumping construction waste into stream.",
            incident_date=timezone.now() - timezone.timedelta(days=1),
            address="Bridge Road, Sector 5",
            reporter=self.user,
            is_anonymous=False,
            contact_email="test@example.org"
        )
        self.assertEqual(report.status, 'submitted')
        self.assertIn(report.reference_id, str(report))
        self.assertIn('bg-slate-100', report.get_status_badge_classes())

    def test_future_incident_date_validation(self):
        future_date = timezone.now() + timezone.timedelta(days=2)
        report = Report(
            title="Future Event",
            category="robbery_theft",
            description="Test future date validation.",
            incident_date=future_date,
            address="Market Square"
        )
        with self.assertRaises(ValidationError):
            report.clean()

    def test_evidence_model_and_size(self):
        report = Report.objects.create(
            title="Corrupt Tender Notice",
            category="corruption_bribery",
            description="Forged signature on procurement sheet.",
            incident_date=timezone.now() - timezone.timedelta(hours=5),
            address="Municipal Office"
        )
        ev = Evidence.objects.create(
            report=report,
            file="evidence/test.pdf",
            original_filename="tender_doc.pdf",
            file_size=2048576, # ~2 MB
            mime_type="application/pdf"
        )
        self.assertEqual(ev.human_readable_size(), "2.0 MB")
        self.assertIn("tender_doc.pdf", str(ev))

    def test_status_history_and_audit(self):
        report = Report.objects.create(
            title="Harassment Incident",
            category="sexual_harassment",
            description="Verbal assault on transit line.",
            incident_date=timezone.now() - timezone.timedelta(hours=2),
            address="Central Subway Station"
        )
        hist = ReportStatusHistory.objects.create(
            report=report,
            previous_status='submitted',
            new_status='under_review',
            changed_by=self.user,
            notes='Review assigned to officer.'
        )
        self.assertEqual(hist.new_status, 'under_review')

        audit = AuditEvent.objects.create(
            user=self.user,
            action='CASE_REVIEWED',
            resource_type='Report',
            resource_id=report.reference_id,
            details='Preliminary assessment conducted.'
        )
        self.assertEqual(audit.action, 'CASE_REVIEWED')

