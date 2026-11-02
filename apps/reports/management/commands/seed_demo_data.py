"""Management command to populate strictly fictional test accounts, departments, tasks, and sample incident records."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from apps.reports.models import Report, ReportStatusHistory, AuditEvent, Department, SystemAnnouncement
from apps.reviews.models import ReviewNote, InvestigationTask
from apps.accounts.models import ReporterProfile

class Command(BaseCommand):
    help = 'Seeds database with fictional test accounts, departments, tasks, and incident reports for development.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding comprehensive demo data..."))

        # 1. Staff Officers
        staff_data = [
            ('officer_smith', 'officer@redflag.internal', 'Sarah', 'Smith', True),
            ('director_vance', 'director@redflag.internal', 'Arthur', 'Vance', True),
            ('investigator_lee', 'lee@redflag.internal', 'Marcus', 'Lee', False),
            ('officer_patel', 'patel@redflag.internal', 'Priya', 'Patel', False),
        ]
        staff_users = {}
        for username, email, first, last, is_super in staff_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': is_super,
                    'first_name': first,
                    'last_name': last
                }
            )
            user.set_password('Password123!')
            user.save()
            staff_users[username] = user

        self.stdout.write(self.style.SUCCESS("Staff accounts verified (Password: Password123!)."))

        # 2. Citizen Reporters
        citizen_data = [
            ('jane_citizen', 'jane@example.org', 'Jane', 'Doe', 'verified', '+1 (555) 321-9876'),
            ('alex_witness', 'alex@example.org', 'Alex', 'Taylor', 'standard', '+1 (555) 789-1234'),
            ('marcus_reporter', 'marcus@example.org', 'Marcus', 'Brody', 'verified', '+1 (555) 456-7890'),
            ('spurious_tester', 'spurious@example.org', 'Spurious', 'Account', 'restricted', '+1 (555) 000-1111'),
        ]
        citizen_users = {}
        for username, email, first, last, trust, phone in citizen_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': False,
                    'is_superuser': False,
                    'first_name': first,
                    'last_name': last
                }
            )
            user.set_password('Password123!')
            user.save()
            citizen_users[username] = user

            # Profile trust
            profile, _ = ReporterProfile.objects.get_or_create(user=user)
            profile.phone = phone
            profile.trust_status = trust
            if trust == 'restricted':
                profile.verification_notes = 'Multiple duplicate filings submitted during testing period.'
            profile.save()

        self.stdout.write(self.style.SUCCESS("Citizen reporter accounts verified (Password: Password123!)."))

        # 3. Nodal Departments
        departments_data = [
            ('Special Cyber Crimes Cell', 'CYBER-CELL', 'National Digital Sphere', 'cyber@redflag.internal', '1930', staff_users['investigator_lee'], 24),
            ('Child Protection & Welfare Committee', 'CHILD-PROT', 'Metropolitan & State', 'childwelfare@redflag.internal', '1098', staff_users['officer_smith'], 12),
            ('Vigilance & Anti-Corruption Bureau', 'VIGILANCE', 'Federal Public Sector', 'vigilance@redflag.internal', '1064', staff_users['director_vance'], 48),
            ('Domestic Violence & Women Safety Cell', 'WOMEN-SAFE', 'District Interventions', 'crisis@redflag.internal', '1091', staff_users['officer_patel'], 12),
            ('Municipal Environmental Compliance', 'ENV-COMP', 'Municipal Water & Air', 'environment@redflag.internal', '+1 (555) 999-3322', staff_users['officer_smith'], 72),
        ]
        departments = {}
        for name, code, juris, email, phone, lead, sla in departments_data:
            dept, _ = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'jurisdiction': juris,
                    'contact_email': email,
                    'contact_phone': phone,
                    'head_officer': lead,
                    'sla_hours': sla,
                    'description': f"Specialized unit responsible for {name.lower()}."
                }
            )
            departments[code] = dept

        self.stdout.write(self.style.SUCCESS("Nodal departments verified."))

        # 4. System Announcements
        if SystemAnnouncement.objects.count() == 0:
            SystemAnnouncement.objects.create(
                title="Heightened Vigilance: Online Digital Financial Phishing Syndicate",
                category="Cyber Crime Advisory",
                content="Reports of coordinated fraudulent SMS messages mimicking municipal taxation portals have surged. Citizens are advised not to click unsolicited links.",
                urgency="warning",
                audience="all",
                created_by=staff_users['director_vance']
            )
            SystemAnnouncement.objects.create(
                title="Priority Directive: Expedited Intake for POCSO and Child Endangerment Claims",
                category="Standard Operating Procedure",
                content="All incoming grievances flagged under Child Abuse must be assigned to an officer and triaged within 2 hours of receipt.",
                urgency="critical",
                audience="staff_only",
                created_by=staff_users['director_vance']
            )
            self.stdout.write(self.style.SUCCESS("System announcements created."))

        # 5. Populate or Update Fictional Cases with priorities & assignments
        sample_cases = [
            {
                'title': 'Unsecured Industrial Chemical Discharge near River Canal',
                'category': 'other',
                'description': 'Witnessed tanker vehicle discharging untreated residue into public canal behind the western municipal rail yard. Noticeable chemical odor observed by neighborhood residents.',
                'incident_date': timezone.now() - timezone.timedelta(days=2, hours=3),
                'address': 'West Canal Bridge, Industrial Sector 4',
                'latitude': 28.6139,
                'longitude': 77.2090,
                'is_anonymous': False,
                'contact_email': 'jane@example.org',
                'contact_phone': '+1 (555) 321-9876',
                'reporter': citizen_users['jane_citizen'],
                'priority': 'high',
                'department': departments['ENV-COMP'],
                'assigned_to': staff_users['officer_smith'],
                'status': 'investigating',
                'is_escalated': False,
                'tasks': [
                    ('Dispatch water sampling field crew', True, staff_users['officer_smith']),
                    ('Verify tanker license plate registry', False, staff_users['investigator_lee']),
                    ('File preliminary environmental citation', False, None)
                ]
            },
            {
                'title': 'Suspected Commercial Extortion Demand on Independent Grocers',
                'category': 'corruption_bribery',
                'description': 'Unidentified individuals claiming departmental enforcement credentials demanding illicit cash payments from independent market vendors to avoid administrative citations.',
                'incident_date': timezone.now() - timezone.timedelta(days=4, hours=6),
                'address': 'North Central Produce Market, Arcade Row',
                'latitude': 28.6200,
                'longitude': 77.2150,
                'is_anonymous': True,
                'contact_email': '',
                'contact_phone': '',
                'reporter': None,
                'priority': 'critical',
                'department': departments['VIGILANCE'],
                'assigned_to': staff_users['director_vance'],
                'status': 'under_review',
                'is_escalated': True,
                'escalation_reason': 'Impending extortion deadline against vulnerable small vendors.',
                'tasks': [
                    ('Cross-check market CCTV footage', True, staff_users['director_vance']),
                    ('Interview market association representatives', False, staff_users['director_vance']),
                ]
            },
            {
                'title': 'Persistent Online Doxxing and Coordinated Digital Threats',
                'category': 'cyber_bullying',
                'description': 'Coordinated harassment campaign publishing private residence photographs and personal telephone records of community volunteer across messaging groups.',
                'incident_date': timezone.now() - timezone.timedelta(days=7),
                'address': 'Digital Network / Online Domain',
                'latitude': None,
                'longitude': None,
                'is_anonymous': False,
                'contact_email': 'jane@example.org',
                'contact_phone': '+1 (555) 321-9876',
                'reporter': citizen_users['jane_citizen'],
                'priority': 'medium',
                'department': departments['CYBER-CELL'],
                'assigned_to': staff_users['investigator_lee'],
                'status': 'resolved',
                'is_escalated': False,
                'resolution_summary': 'Takedown notices issued under statutory provisions. Offending group de-indexed and perpetrators cautioned.',
                'tasks': [
                    ('Issue formal preservation notice to platform host', True, staff_users['investigator_lee']),
                    ('Verify takedown confirmation', True, staff_users['investigator_lee'])
                ]
            },
            {
                'title': 'Repeated Domestic Distress Calls Unaddressed in Apartment Complex',
                'category': 'domestic_violence',
                'description': 'Neighbor reporting audible distress and calls for help from unit 4B over consecutive evenings. Previous welfare inquiries were met with refusal to open door.',
                'incident_date': timezone.now() - timezone.timedelta(hours=14),
                'address': 'Oakwood Heights Apartment 4B, 12 Elm Street',
                'latitude': 28.6050,
                'longitude': 77.2100,
                'is_anonymous': True,
                'contact_email': '',
                'contact_phone': '',
                'reporter': None,
                'priority': 'critical',
                'department': departments['WOMEN-SAFE'],
                'assigned_to': staff_users['officer_patel'],
                'status': 'submitted',
                'is_escalated': True,
                'escalation_reason': 'Active physical distress reported over multiple consecutive evenings.',
                'tasks': [
                    ('Contact local police precinct for welfare check dispatch', False, staff_users['officer_patel']),
                    ('Request building management access log', False, None)
                ]
            },
            {
                'title': 'Unlawful Child Labor in Brick Kiln Facility',
                'category': 'child_abuse',
                'description': 'Multiple school-aged minors observed transporting heavy clay molds in industrial kiln facility during standard school hours without protective equipment.',
                'incident_date': timezone.now() - timezone.timedelta(days=1, hours=8),
                'address': 'Eastern Industrial Perimeter, Kiln Yard 3',
                'latitude': 28.5900,
                'longitude': 77.2300,
                'is_anonymous': False,
                'contact_email': 'alex@example.org',
                'contact_phone': '+1 (555) 789-1234',
                'reporter': citizen_users['alex_witness'],
                'priority': 'critical',
                'department': departments['CHILD-PROT'],
                'assigned_to': staff_users['officer_smith'],
                'status': 'investigating',
                'is_escalated': True,
                'escalation_reason': 'Child endangerment and non-compliance with statutory education mandates.',
                'tasks': [
                    ('Coordinated joint inspection with district labor commissioner', True, staff_users['officer_smith']),
                    ('Medical assessment and child rehabilitation referral', False, staff_users['officer_smith'])
                ]
            },
            {
                'title': 'Suspected Counterfeit Prescription Pharmaceuticals Operation',
                'category': 'drug_trafficking',
                'description': 'Unlicensed storefront distributing blister packs of antibiotics and analgesics without manufacturer lot numbers or pharmacist oversight.',
                'incident_date': timezone.now() - timezone.timedelta(days=5),
                'address': 'Old Bazaar Alleyway, Shop 19',
                'latitude': 28.6300,
                'longitude': 77.2100,
                'is_anonymous': False,
                'contact_email': 'marcus@example.org',
                'contact_phone': '+1 (555) 456-7890',
                'reporter': citizen_users['marcus_reporter'],
                'priority': 'high',
                'department': departments['CYBER-CELL'],
                'assigned_to': staff_users['investigator_lee'],
                'status': 'under_review',
                'is_escalated': False,
                'tasks': [
                    ('Refer sample to State Drug Testing Laboratory', False, staff_users['investigator_lee'])
                ]
            }
        ]

        for case_data in sample_cases:
            report, created = Report.objects.get_or_create(
                title=case_data['title'],
                defaults={
                    'category': case_data['category'],
                    'description': case_data['description'],
                    'incident_date': case_data['incident_date'],
                    'address': case_data['address'],
                    'latitude': case_data.get('latitude'),
                    'longitude': case_data.get('longitude'),
                    'is_anonymous': case_data['is_anonymous'],
                    'contact_email': case_data['contact_email'],
                    'contact_phone': case_data['contact_phone'],
                    'reporter': case_data['reporter'],
                    'priority': case_data['priority'],
                    'department': case_data['department'],
                    'assigned_to': case_data['assigned_to'],
                    'status': case_data['status'],
                    'is_escalated': case_data.get('is_escalated', False),
                    'escalation_reason': case_data.get('escalation_reason', ''),
                    'resolution_summary': case_data.get('resolution_summary', ''),
                }
            )

            # If existing, update priority & department
            if not created:
                report.priority = case_data['priority']
                report.department = case_data['department']
                report.assigned_to = case_data['assigned_to']
                report.is_escalated = case_data.get('is_escalated', False)
                report.escalation_reason = case_data.get('escalation_reason', '')
                report.resolution_summary = case_data.get('resolution_summary', '')
                report.save()

            # Ensure tasks
            for task_title, is_done, assigned_user in case_data.get('tasks', []):
                t, _ = InvestigationTask.objects.get_or_create(
                    report=report,
                    title=task_title,
                    defaults={
                        'is_completed': is_done,
                        'assigned_to': assigned_user,
                        'completed_by': assigned_user if is_done else None,
                        'completed_at': timezone.now() if is_done else None
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Seeded/Updated {len(sample_cases)} comprehensive incident cases with tasks & assignments."))
