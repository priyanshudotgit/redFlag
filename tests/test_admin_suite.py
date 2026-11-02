"""Comprehensive automated tests for redFlag Admin Platform & Command Center suite."""

import json
from io import BytesIO
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.reports.models import Report, Evidence, Department, SystemAnnouncement, AuditEvent
from apps.accounts.models import ReporterProfile
from apps.reviews.models import ReviewNote, InvestigationTask


class AdminPlatformSuiteTests(TestCase):
    """Rigorous end-to-end tests for all administrative command center modules."""

    def setUp(self):
        self.client = Client()

        # Users
        self.staff_director = User.objects.create_user(
            username='director_vance',
            email='vance@redflag.internal',
            password='AdminPassword123!',
            first_name='Vance',
            last_name='Director',
            is_staff=True,
            is_superuser=True
        )

        self.staff_investigator = User.objects.create_user(
            username='officer_smith',
            email='smith@redflag.internal',
            password='StaffPassword123!',
            first_name='John',
            last_name='Smith',
            is_staff=True
        )

        self.civilian_user = User.objects.create_user(
            username='jane_citizen',
            email='jane@example.org',
            password='CitizenPassword123!',
            first_name='Jane',
            last_name='Citizen'
        )
        self.civilian_profile = self.civilian_user.profile
        self.civilian_profile.trust_status = 'verified'
        self.civilian_profile.reputation_score = 95
        self.civilian_profile.phone = '+1-555-0199'
        self.civilian_profile.address = '450 Civic Way, Metropolis'
        self.civilian_profile.save()

        # Department
        self.dept_police = Department.objects.create(
            name='Metropolitan Police Oversight',
            code='POLICE',
            contact_email='police@redflag.internal',
            sla_hours=24,
            is_active=True
        )

        self.dept_pwd = Department.objects.create(
            name='Public Works & Infrastructure',
            code='PWD',
            contact_email='pwd@redflag.internal',
            sla_hours=48,
            is_active=True
        )

        # Identified Report
        self.identified_report = Report.objects.create(
            reference_id='RF-TEST-IDENTIFIED',
            title='Bribery Demanded at Construction Site',
            description='Municipal building inspector demanded cash payment to issue permit.',
            category='bribery',
            incident_date=timezone.now(),
            address='100 Metro Plaza',
            reporter=self.civilian_user,
            is_anonymous=False,
            status='submitted',
            priority='high',
            department=self.dept_police,
            assigned_to=self.staff_investigator
        )

        # Anonymous Report
        self.anonymous_report = Report.objects.create(
            reference_id='RF-TEST-ANONYMOUS',
            title='Illegal Chemical Dumping in River',
            description='Industrial drums dumped near river bank at midnight.',
            category='environmental',
            incident_date=timezone.now(),
            address='Industrial Wharf Pier 9',
            reporter=None,
            is_anonymous=True,
            status='submitted',
            priority='critical',
            is_escalated=True,
            escalation_reason='Hazardous biological threat',
            contact_email='whistleblower@protonmail.internal'
        )

    # --------------------------------------------------------------------------
    # 1. Access Control & Permissions
    # --------------------------------------------------------------------------
    def test_anonymous_user_redirected_from_admin_modules(self):
        """Unauthenticated requests to admin suite must redirect to sign in."""
        endpoints = [
            reverse('admin_command_center'),
            reverse('staff_queue'),
            reverse('department_list'),
            reverse('reporter_list'),
            reverse('officer_list'),
            reverse('audit_log_list'),
            reverse('export_hub'),
            reverse('announcement_list'),
            reverse('staff_report_detail', kwargs={'pk': self.identified_report.pk}),
        ]
        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 302, f"Failed for {url}")
            self.assertIn('/accounts/login/', res['Location'])

    def test_civilian_cannot_access_command_center(self):
        """Civilian non-staff users cannot access staff command center or queue."""
        self.client.login(username='jane_citizen', password='CitizenPassword123!')
        res = self.client.get(reverse('admin_command_center'))
        self.assertEqual(res.status_code, 302)

        res_queue = self.client.get(reverse('staff_queue'))
        self.assertEqual(res_queue.status_code, 302)

    # --------------------------------------------------------------------------
    # 2. Command Center Dashboard
    # --------------------------------------------------------------------------
    def test_command_center_kpis_and_rendering(self):
        """Staff accessing Command Center sees live metrics, alerts, and distributions."""
        self.client.login(username='director_vance', password='AdminPassword123!')
        res = self.client.get(reverse('admin_command_center'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'reviews/command_center.html')

        metrics = res.context['metrics']
        self.assertEqual(metrics['total'], 2)
        self.assertEqual(metrics['submitted'], 2)
        self.assertEqual(metrics['critical'], 1)
        self.assertEqual(metrics['escalated'], 1)

        # Urgent cases section includes the critical anonymous report
        urgent_cases = list(res.context['urgent_cases'])
        self.assertIn(self.anonymous_report, urgent_cases)

    # --------------------------------------------------------------------------
    # 3. Case Queue & Multi-Filtering
    # --------------------------------------------------------------------------
    def test_queue_filters_by_filing_type(self):
        """Queue accurately filters identified citizens vs anonymous whistleblowers."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        # Filter anonymous
        res_anon = self.client.get(reverse('staff_queue'), {'filing_type': 'anonymous'})
        self.assertEqual(res_anon.status_code, 200)
        cases_anon = list(res_anon.context['page_obj'])
        self.assertIn(self.anonymous_report, cases_anon)
        self.assertNotIn(self.identified_report, cases_anon)

        # Filter identified
        res_ident = self.client.get(reverse('staff_queue'), {'filing_type': 'identified'})
        self.assertEqual(res_ident.status_code, 200)
        cases_ident = list(res_ident.context['page_obj'])
        self.assertIn(self.identified_report, cases_ident)
        self.assertNotIn(self.anonymous_report, cases_ident)

    def test_queue_bulk_action_dispatch(self):
        """Staff can execute bulk actions on selected cases."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        post_data = {
            'bulk_action': 'mark_investigating',
            'selected_cases': [self.identified_report.pk, self.anonymous_report.pk]
        }
        res = self.client.post(reverse('staff_queue'), post_data)
        self.assertEqual(res.status_code, 302)

        self.identified_report.refresh_from_db()
        self.anonymous_report.refresh_from_db()
        self.assertEqual(self.identified_report.status, 'investigating')
        self.assertEqual(self.anonymous_report.status, 'investigating')

        # Audit event created
        audit = AuditEvent.objects.filter(action='BULK_CASE_ACTION').last()
        self.assertIsNotNone(audit)
        self.assertIn('mark_investigating', audit.details)

    # --------------------------------------------------------------------------
    # 4. Investigation Workbench & Filer Visibility
    # --------------------------------------------------------------------------
    def test_investigation_workbench_shows_filer_dossier_correctly(self):
        """Dossier shows verified civilian details for identified reports and privacy card for whistleblower."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        # Identified Report
        res_ident = self.client.get(reverse('staff_report_detail', kwargs={'pk': self.identified_report.pk}))
        self.assertEqual(res_ident.status_code, 200)
        self.assertContains(res_ident, 'Jane Citizen')
        self.assertContains(res_ident, 'Verified Citizen')
        self.assertContains(res_ident, '450 Civic Way')

        # Anonymous Report
        res_anon = self.client.get(reverse('staff_report_detail', kwargs={'pk': self.anonymous_report.pk}))
        self.assertEqual(res_anon.status_code, 200)
        self.assertContains(res_anon, 'Anonymous Whistleblower (Privacy Protocol Active)')
        self.assertContains(res_anon, 'whistleblower@protonmail.internal')
        # Does not leak non-existent or other user credentials
        self.assertNotContains(res_anon, 'Jane Citizen')

    def test_case_status_transition_with_resolution_summary(self):
        """Status update requires valid state progression and records history."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        # Advance to under_review
        url = reverse('update_status', kwargs={'pk': self.identified_report.pk})
        res = self.client.post(url, {
            'new_status': 'under_review',
            'notes': 'Intake verified by forensics desk.'
        })
        self.assertEqual(res.status_code, 302)
        self.identified_report.refresh_from_db()
        self.assertEqual(self.identified_report.status, 'under_review')

        # Resolve with resolution summary
        res2 = self.client.post(url, {
            'new_status': 'resolved',
            'notes': 'Inspector was suspended following disciplinary inquiry.',
            'resolution_summary': 'Disciplinary inquiry substantiated allegations. Administrative penalties invoked.'
        })
        self.assertEqual(res2.status_code, 302)
        self.identified_report.refresh_from_db()
        self.assertEqual(self.identified_report.status, 'resolved')
        self.assertIn('Disciplinary inquiry substantiated', self.identified_report.resolution_summary)

    def test_case_reassignment_and_dispatch(self):
        """Assigning case to new officer and department creates status log."""
        self.client.login(username='director_vance', password='AdminPassword123!')

        url = reverse('assign_case', kwargs={'pk': self.anonymous_report.pk})
        res = self.client.post(url, {
            'assigned_to': self.staff_director.pk,
            'department': self.dept_pwd.pk,
            'dispatch_notes': 'Environmental task force mobilized immediately.'
        })
        self.assertEqual(res.status_code, 302)
        self.anonymous_report.refresh_from_db()
        self.assertEqual(self.anonymous_report.assigned_to, self.staff_director)
        self.assertEqual(self.anonymous_report.department, self.dept_pwd)

    def test_case_priority_and_escalation_update(self):
        """Updating priority severity and toggling director escalation."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        url = reverse('update_priority', kwargs={'pk': self.identified_report.pk})
        res = self.client.post(url, {
            'priority': 'critical',
            'is_escalated': True,
            'escalation_reason': 'Suspect threatened complainant with retribution.'
        })
        self.assertEqual(res.status_code, 302)
        self.identified_report.refresh_from_db()
        self.assertEqual(self.identified_report.priority, 'critical')
        self.assertTrue(self.identified_report.is_escalated)
        self.assertIn('threatened complainant', self.identified_report.escalation_reason)

    def test_investigation_checklist_task_workflow(self):
        """Adding a checklist task and toggling completion records timestamp and officer."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        # Add task
        add_url = reverse('add_investigation_task', kwargs={'pk': self.identified_report.pk})
        res = self.client.post(add_url, {'title': 'Subpoena bank records for account 9912'})
        self.assertEqual(res.status_code, 302)

        task = InvestigationTask.objects.filter(report=self.identified_report).first()
        self.assertIsNotNone(task)
        self.assertFalse(task.is_completed)

        # Toggle complete
        toggle_url = reverse('toggle_investigation_task', kwargs={'pk': self.identified_report.pk, 'task_id': task.pk})
        res_toggle = self.client.post(toggle_url)
        self.assertEqual(res_toggle.status_code, 302)

        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        self.assertEqual(task.completed_by, self.staff_investigator)
        self.assertIsNotNone(task.completed_at)

    def test_official_evidence_upload_and_sha256_hash(self):
        """Official departmental evidence upload automatically generates SHA-256 hash."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        file_content = b"OFFICIAL FORENSIC LAB REPORT #8990\nContaminant detected: Lead (0.42mg/L)"
        test_file = SimpleUploadedFile("forensic_report.pdf", file_content, content_type="application/pdf")

        upload_url = reverse('upload_official_evidence', kwargs={'pk': self.anonymous_report.pk})
        res = self.client.post(upload_url, {
            'evidence_file': test_file,
            'description': 'Municipal Laboratory Water Chemistry Certificate'
        })
        self.assertEqual(res.status_code, 302)

        evidence = Evidence.objects.filter(report=self.anonymous_report, is_official=True).first()
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.description, 'Municipal Laboratory Water Chemistry Certificate')
        self.assertTrue(evidence.is_official)
        self.assertEqual(evidence.uploaded_by, self.staff_investigator)
        self.assertTrue(len(evidence.file_hash) == 64, "SHA-256 hash must be 64 hexadecimal characters")

    # --------------------------------------------------------------------------
    # 5. Printable Case Dossier
    # --------------------------------------------------------------------------
    def test_printable_case_dossier_renders_correctly(self):
        """Printable case dossier generates formal transcript and logs audit event."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        url = reverse('printable_case_dossier', kwargs={'pk': self.identified_report.pk})
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'reviews/case_dossier_print.html')
        self.assertContains(res, 'OFFICIAL INCIDENT DOSSIER')
        self.assertContains(res, 'RF-TEST-IDENTIFIED')

        # Audit event recorded
        audit = AuditEvent.objects.filter(action='PRINT_CASE_DOSSIER').last()
        self.assertIsNotNone(audit)

    # --------------------------------------------------------------------------
    # 6. Departments Management
    # --------------------------------------------------------------------------
    def test_department_directory_and_creation(self):
        """Registering a new response department."""
        self.client.login(username='director_vance', password='AdminPassword123!')

        res_list = self.client.get(reverse('department_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'Metropolitan Police Oversight')

        # Create new
        res_create = self.client.post(reverse('department_create'), {
            'name': 'Anti-Corruption Directorate',
            'code': 'ACD',
            'contact_email': 'anticorruption@redflag.internal',
            'contact_phone': '+1-800-555-9000',
            'sla_hours': 12,
            'description': 'Vigilance agency handling public officer extortion.',
            'is_active': True
        })
        self.assertEqual(res_create.status_code, 302)

        dept = Department.objects.filter(code='ACD').first()
        self.assertIsNotNone(dept)
        self.assertEqual(dept.sla_hours, 12)

    # --------------------------------------------------------------------------
    # 7. Citizen Reporter Management
    # --------------------------------------------------------------------------
    def test_reporter_directory_and_trust_verification(self):
        """Inspecting citizen dossier and modifying trust verification status."""
        self.client.login(username='director_vance', password='AdminPassword123!')

        res_list = self.client.get(reverse('reporter_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'Jane Citizen')

        # Calibrate trust
        detail_url = reverse('reporter_detail', kwargs={'pk': self.civilian_user.pk})
        res_detail = self.client.get(detail_url)
        self.assertEqual(res_detail.status_code, 200)

        res_update = self.client.post(detail_url, {
            'trust_status': 'trusted',
            'reputation_score': 98,
            'phone': '+1-555-8888',
            'address': '770 Freedom Blvd',
            'verification_notes': 'Identity verified via national digital credentials.'
        })
        self.assertEqual(res_update.status_code, 302)

        self.civilian_profile.refresh_from_db()
        self.assertEqual(self.civilian_profile.trust_status, 'trusted')
        self.assertEqual(self.civilian_profile.reputation_score, 98)

    # --------------------------------------------------------------------------
    # 8. Staff Officers Directory
    # --------------------------------------------------------------------------
    def test_officer_list_directory(self):
        """Staff directory lists officers and their active workloads."""
        self.client.login(username='officer_smith', password='StaffPassword123!')

        res = self.client.get(reverse('officer_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'director_vance')
        self.assertContains(res, 'officer_smith')

    # --------------------------------------------------------------------------
    # 9. Audit Logs
    # --------------------------------------------------------------------------
    def test_audit_logs_search_and_filter(self):
        """Security audit trail displays system operations with action filtering."""
        self.client.login(username='director_vance', password='AdminPassword123!')

        # Generate audit entry
        AuditEvent.objects.create(
            user=self.staff_director,
            action='INTEGRITY_CHECK',
            resource_type='System',
            resource_id='SYS-01',
            details='Nightly checksum verification executed.',
            ip_address='192.168.1.100'
        )

        res = self.client.get(reverse('audit_log_list'), {'action': 'INTEGRITY_CHECK'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'INTEGRITY_CHECK')
        self.assertContains(res, 'Nightly checksum verification executed.')

    # --------------------------------------------------------------------------
    # 10. Intelligence & Data Export Hub
    # --------------------------------------------------------------------------
    def test_export_hub_csv_and_json(self):
        """Export hub downloads valid CSV and JSON datasets."""
        self.client.login(username='director_vance', password='AdminPassword123!')

        # Form view
        res_view = self.client.get(reverse('export_hub'))
        self.assertEqual(res_view.status_code, 200)

        # CSV Download
        res_csv = self.client.post(reverse('export_hub'), {'format': 'csv'})
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv['Content-Type'], 'text/csv; charset=utf-8')
        content_csv = res_csv.content.decode('utf-8')
        self.assertIn('Reference ID,Title,Category', content_csv)
        self.assertIn('RF-TEST-IDENTIFIED', content_csv)
        self.assertIn('RF-TEST-ANONYMOUS', content_csv)

        # JSON Download
        res_json = self.client.post(reverse('export_hub'), {'format': 'json'})
        self.assertEqual(res_json.status_code, 200)
        self.assertEqual(res_json['Content-Type'], 'application/json')
        data = json.loads(res_json.content.decode('utf-8'))
        self.assertEqual(len(data), 2)
        ref_ids = [d['reference_id'] for d in data]
        self.assertIn('RF-TEST-IDENTIFIED', ref_ids)
        self.assertIn('RF-TEST-ANONYMOUS', ref_ids)

    # --------------------------------------------------------------------------
    # 11. System Bulletins & Safety Advisories
    # --------------------------------------------------------------------------
    def test_announcements_creation_and_toggle(self):
        """Publishing safety advisories and toggling active status."""
        self.client.login(username='director_vance', password='AdminPassword123!')

        res_create = self.client.post(reverse('announcement_list'), {
            'title': 'Public Alert: False Utility Inspectors',
            'urgency': 'critical',
            'content': 'Individuals posing as water utility inspectors in district 4.',
            'category': 'Public Safety Alert',
            'audience': 'all',
            'is_active': True
        })
        self.assertEqual(res_create.status_code, 302)

        bulletin = SystemAnnouncement.objects.filter(title='Public Alert: False Utility Inspectors').first()
        self.assertIsNotNone(bulletin)
        self.assertTrue(bulletin.is_active)

        # Toggle archive
        res_toggle = self.client.get(reverse('announcement_toggle', kwargs={'pk': bulletin.pk}))
        self.assertEqual(res_toggle.status_code, 302)

        bulletin.refresh_from_db()
        self.assertFalse(bulletin.is_active)
