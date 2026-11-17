"""Management command to populate authentic Indian civic grievances, abuse reports, and calibrate superadmins."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from apps.reports.models import Report, ReportStatusHistory, AuditEvent, Department, SystemAnnouncement
from apps.reviews.models import ReviewNote, InvestigationTask
from apps.accounts.models import ReporterProfile

class Command(BaseCommand):
    help = 'Seeds database with realistic Indian civic grievances, public abuse complaints, and exactly 2 superadmins (admin1, admin2).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing Indian civic grievances database calibration..."))

        # ----------------------------------------------------------------------
        # 1. Superadmins (Strictly 2 Superadmins: admin1 and admin2, password: 'admin')
        # ----------------------------------------------------------------------
        superadmins = [
            ('admin1', 'admin1@redflag.gov.in', 'Vikram', 'Rathore'),
            ('admin2', 'admin2@redflag.gov.in', 'Ananya', 'Deshmukh'),
        ]
        admin_users = {}
        for username, email, first, last in superadmins:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                    'first_name': first,
                    'last_name': last,
                }
            )
            user.set_password('admin')
            user.is_staff = True
            user.is_superuser = True
            user.first_name = first
            user.last_name = last
            user.email = email
            user.save()
            admin_users[username] = user

        # Demote all other users so ONLY admin1 and admin2 have is_superuser=True
        demoted = User.objects.filter(is_superuser=True).exclude(username__in=['admin1', 'admin2']).update(is_superuser=False)
        self.stdout.write(self.style.SUCCESS(f"Calibrated 2 Superadmins: admin1, admin2 (Password: 'admin'). Demoted {demoted} other accounts."))

        # ----------------------------------------------------------------------
        # 2. Investigating Officers (Staff Members: is_staff=True, is_superuser=False)
        # ----------------------------------------------------------------------
        staff_officers_data = [
            ('inspector_verma', 'verma@redflag.gov.in', 'Rajesh', 'Verma'),
            ('officer_sharma', 'sharma@redflag.gov.in', 'Sunita', 'Sharma'),
            ('inspector_singh', 'singh@redflag.gov.in', 'Hardeep', 'Singh'),
        ]
        staff_users = {**admin_users}
        for username, email, first, last in staff_officers_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': False,
                    'first_name': first,
                    'last_name': last,
                }
            )
            user.set_password('Password123!')
            user.is_staff = True
            user.is_superuser = False
            user.save()
            staff_users[username] = user

        self.stdout.write(self.style.SUCCESS("Investigating officers verified."))

        # ----------------------------------------------------------------------
        # 3. Citizen Reporters (Indian citizens with real verification statuses)
        # ----------------------------------------------------------------------
        citizens_data = [
            ('rohit_kumar', 'rohit.kumar@gmail.com', 'Rohit', 'Kumar', 'verified', '+91 98101 23456', 'Flat 402, Shivalik Apartments, Sector 62, Noida, Uttar Pradesh - 201309', 96),
            ('priya_nair', 'priya.nair@outlook.in', 'Priya', 'Nair', 'verified', '+91 97455 67890', '14/B, 3rd Cross, 100 Feet Road, Indiranagar, Bengaluru, Karnataka - 560038', 98),
            ('arjun_mehta', 'arjun.mehta@yahoo.co.in', 'Arjun', 'Mehta', 'standard', '+91 98200 11223', 'B-201, Crystal Plaza, New Link Road, Andheri West, Mumbai, Maharashtra - 400053', 80),
            ('ananya_sen', 'ananya.sen@gmail.com', 'Ananya', 'Sen', 'standard', '+91 98300 44556', 'Block CF-182, Sector 1, Salt Lake City, Kolkata, West Bengal - 700064', 72),
            ('kavita_reddy', 'kavita.reddy@gmail.com', 'Kavita', 'Reddy', 'verified', '+91 99490 88776', 'Plot 45, Road No. 12, Banjara Hills, Hyderabad, Telangana - 500034', 91),
        ]
        citizen_users = {}
        for username, email, first, last, trust, phone, address, score in citizens_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': False,
                    'is_superuser': False,
                    'first_name': first,
                    'last_name': last,
                }
            )
            user.set_password('Password123!')
            user.save()
            citizen_users[username] = user

            profile, _ = ReporterProfile.objects.get_or_create(user=user)
            profile.phone = phone
            profile.address = address
            profile.trust_status = trust
            profile.reputation_score = score
            profile.verification_notes = f'Identity and phone number verified via Indian Aadhaar / Mobile OTP KYC.'
            profile.save()

        self.stdout.write(self.style.SUCCESS("Indian citizen reporters initialized."))

        # ----------------------------------------------------------------------
        # 4. Indian Nodal Departments & Public Authorities
        # ----------------------------------------------------------------------
        departments_data = [
            (
                'Special Cyber Crime Cell (NCRP 1930)',
                'CYBER-CELL',
                'National Cyber Crime Reporting Portal (NCRP), New Delhi',
                'cybercell-inquiry@gov.in',
                '1930',
                admin_users['admin1'],
                24,
                'Specialized operational unit responsible for online cyber fraud, trans-state digital arrest scams, and financial phishing forensics under IT Act Section 66D.'
            ),
            (
                'Anti-Corruption & Public Vigilance Directorate',
                'CVC-VIGILANCE',
                'Central Vigilance Commission & State Anti-Corruption Bureaus',
                'vigilance.directorate@nic.in',
                '1064',
                admin_users['admin1'],
                48,
                'Independent oversight bureau investigating extortion, illicit bribes, kickbacks, and procurement malpractices under Prevention of Corruption Act.'
            ),
            (
                'Women Safety & Anti-Harassment Special Cell (NCW)',
                'WOMEN-SAFETY',
                'National Commission for Women 24/7 Rapid Response Grid',
                'womensafety.helpline@gov.in',
                '1091',
                admin_users['admin2'],
                12,
                'Emergency nodal cell handling domestic violence, stalking, physical abuse, and crisis shelter interventions under PWDVA 2005.'
            ),
            (
                'Child Protection & Anti-Trafficking Commission (Childline)',
                'NCPCR-CHILD',
                'National Commission for Protection of Child Rights (NCPCR)',
                'childline1098@gov.in',
                '1098',
                admin_users['admin2'],
                12,
                'Statutory commission for emergency child rescue, hazardous child labor prohibition, and POCSO case monitoring.'
            ),
            (
                'Central Pollution Control & Environmental Vigilance (NGT)',
                'CPCB-ENV',
                'National Green Tribunal (NGT) Statutory Compliance Grid',
                'cpcb.enforcement@nic.in',
                '011-43102030',
                admin_users['admin1'],
                72,
                'Enforcement authority monitoring industrial effluent discharge, hazardous chemical emissions, and municipal water body conservation.'
            ),
            (
                'Municipal Corporation Grievance & Public Safety Cell',
                'MCD-CIVIC',
                'Zonal Municipal Corporations (MCD / BBMP / BMC / GCC)',
                'grievance@mcd.gov.in',
                '155304',
                admin_users['admin2'],
                48,
                'Civic grievance wing handling urban infrastructure hazards, uncovered stormwater manholes, road safety collapses, and sanitation bottlenecks.'
            ),
        ]
        departments = {}
        for name, code, juris, email, phone, lead, sla, desc in departments_data:
            dept, _ = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'jurisdiction': juris,
                    'contact_email': email,
                    'contact_phone': phone,
                    'head_officer': lead,
                    'sla_hours': sla,
                    'description': desc
                }
            )
            # Update existing department fields
            dept.name = name
            dept.jurisdiction = juris
            dept.contact_email = email
            dept.contact_phone = phone
            dept.head_officer = lead
            dept.sla_hours = sla
            dept.description = desc
            dept.save()
            departments[code] = dept

        self.stdout.write(self.style.SUCCESS("Indian nodal public departments updated."))

        # ----------------------------------------------------------------------
        # 5. National System Announcements & Bulletins
        # ----------------------------------------------------------------------
        SystemAnnouncement.objects.all().delete()
        SystemAnnouncement.objects.create(
            title="National Cyber Advisory: Massive Surge in Fraudulent 'Digital Arrest' Video-Calls & Electricity Bill Disconnection APKs",
            category="Cyber Security Advisory",
            content="Organized inter-state cyber syndicates impersonating CBI, ED, and State Police are coercing citizens over Skype/WhatsApp video calls under fabricated 'Digital Arrest' threats. Never transfer funds or download third-party .apk files. Report immediate extortion to National Cyber Crime Helpline 1930.",
            urgency="critical",
            audience="all",
            created_by=admin_users['admin1']
        )
        SystemAnnouncement.objects.create(
            title="Priority Directive: Mandatory 2-Hour Escalation SLA for Child Abuse (POCSO) and Domestic Emergency Distress Signals",
            category="Standard Operating Procedure",
            content="All incoming grievances flagged under Child Abuse (POCSO) or Domestic Distress must be triaged by an on-duty officer within 2 hours. Mandatory coordination with Child Welfare Committee (CWC) or District Protection Officer must be documented in case notes.",
            urgency="critical",
            audience="staff_only",
            created_by=admin_users['admin2']
        )
        SystemAnnouncement.objects.create(
            title="Anti-Corruption Circular: Zero-Tolerance Policy on Extortion and Illegal Gratification in Civic Trade Licenses & Municipal NOCs",
            category="Public Vigilance Directive",
            content="Demanding cash bribes or facilitating private touts for official revenue records, property mutations, or fire safety NOCs is a non-bailable offense under Section 7 of the Prevention of Corruption Act. Citizens are urged to upload audio/video evidence directly through redFlag.",
            urgency="warning",
            audience="all",
            created_by=admin_users['admin1']
        )
        self.stdout.write(self.style.SUCCESS("National system bulletins and advisories published."))

        # ----------------------------------------------------------------------
        # 6. Realistic Indian Complaints & Civic Grievance Reports
        # ----------------------------------------------------------------------
        # Clear existing cases to ensure a completely clean, authentic Indian dataset
        Report.objects.all().delete()

        sample_cases = [
            {
                'title': 'Severe Untreated Chemical Effluent Discharge into Hindon River & Underground Aquifers',
                'category': 'other',
                'description': 'Commercial textile dyeing and zinc electroplating factory secretly discharging untreated, heavy-metal laden toxic effluent through an unmapped underground concrete conduit directly into the Hindon River tributary between 1:00 AM and 4:30 AM every night. Groundwater in neighboring residential societies has turned pale yellow with a pungent chemical odor. Borewell TDS exceeds 3,400 ppm, posing an immediate health threat to over 15,000 residents.',
                'incident_date': timezone.now() - timezone.timedelta(days=1, hours=4),
                'address': 'Plot 84-B, Mohan Nagar Industrial Area, Ghaziabad, Uttar Pradesh - 201007',
                'latitude': 28.6792,
                'longitude': 77.3879,
                'is_anonymous': False,
                'contact_email': 'rohit.kumar@gmail.com',
                'contact_phone': '+91 98101 23456',
                'reporter': citizen_users['rohit_kumar'],
                'priority': 'critical',
                'department': departments['CPCB-ENV'],
                'assigned_to': admin_users['admin1'],
                'status': 'investigating',
                'is_escalated': True,
                'escalation_reason': 'High risk of toxic heavy metal contamination into municipal groundwater aquifer.',
                'tasks': [
                    ('Collect certified effluent water samples at Mohan Nagar conduit outlet', True, staff_users['inspector_singh']),
                    ('Issue immediate electricity & water disconnection notice via UP Pollution Control Board', False, admin_users['admin1']),
                    ('File statutory prosecution petition before National Green Tribunal (NGT) Principal Bench', False, None)
                ],
                'notes': [
                    (admin_users['admin1'], 'UPPCB Regional Office Ghaziabad alerted. Joint inspection team mobilized for midnight raid on factory premises.')
                ]
            },
            {
                'title': 'Extortion and Coercive Bribe Demand for Issuance of Death Certificate & Land Mutation',
                'category': 'corruption_bribery',
                'description': 'Sub-Registrar record keeper and private touts operating outside Counter No. 4 demanding ₹35,000 cash bribe to release legitimate legal heir mutation documents and certified succession registry. Complainant family has made 6 physical visits with computerized hospital records verified, yet files are deliberately withheld unless kickback is paid.',
                'incident_date': timezone.now() - timezone.timedelta(days=3, hours=7),
                'address': 'Tehsil Sub-Registrar Office, Mehrauli Badarpur Road, Saket, South Delhi - 110030',
                'latitude': 28.5204,
                'longitude': 77.2014,
                'is_anonymous': True,
                'contact_email': '',
                'contact_phone': '',
                'reporter': None,
                'priority': 'high',
                'department': departments['CVC-VIGILANCE'],
                'assigned_to': admin_users['admin1'],
                'status': 'under_review',
                'is_escalated': True,
                'escalation_reason': 'Systemic extortion racket operating with touts outside government sub-registrar office.',
                'tasks': [
                    ('Verify digital application timestamps on Delhi e-District portal', True, staff_users['inspector_singh']),
                    ('Summon Sub-Registrar Saket for preliminary administrative inquiry', False, admin_users['admin1']),
                    ('Deploy Anti-Corruption Bureau decoy surveillance team at Saket registry counters', False, staff_users['inspector_singh'])
                ],
                'notes': [
                    (admin_users['admin1'], 'Verified digital filing token #DL-2026-9921 was held up for 42 days without statutory objection recorded.')
                ]
            },
            {
                'title': 'Trans-National "Digital Arrest" & Cyber Extortion Gang Targeting Senior Citizens',
                'category': 'cyber_bullying',
                'description': 'Organized cyber syndicate impersonating Enforcement Directorate (ED) and Telecom Regulatory Authority of India (TRAI) officers conducted a 72-hour coercive video-call "digital arrest" against a 74-year-old retired ISRO scientist. Perpetrators fabricated fake Supreme Court warrants and extorted ₹18,40,000 via RTGS into fraudulent mule accounts before family detected the fraud.',
                'incident_date': timezone.now() - timezone.timedelta(days=5),
                'address': 'Flat 304, Palm Grove Enclave, Indiranagar 100 Feet Road, Bengaluru, Karnataka - 560038',
                'latitude': 12.9719,
                'longitude': 77.6412,
                'is_anonymous': False,
                'contact_email': 'priya.nair@outlook.in',
                'contact_phone': '+91 97455 67890',
                'reporter': citizen_users['priya_nair'],
                'priority': 'critical',
                'department': departments['CYBER-CELL'],
                'assigned_to': admin_users['admin1'],
                'status': 'investigating',
                'is_escalated': True,
                'escalation_reason': 'Active multi-state money laundering syndicate exploiting senior citizen life savings.',
                'tasks': [
                    ('Initiate emergency 1930 NCRP beneficiary bank account lien freeze', True, staff_users['inspector_verma']),
                    ('Subpoena bank manager for KYC and withdrawal logs of mule account in Surat', True, staff_users['inspector_verma']),
                    ('Register formal FIR under Section 318(4) BNS and Section 66D IT Act', False, staff_users['inspector_verma']),
                    ('Coordinate with Interpol National Central Bureau for international IP traces', False, None)
                ],
                'notes': [
                    (staff_users['inspector_verma'], 'Successfully frozen ₹11.2 Lakhs in primary mule bank account at Surat branch. Balance transferred through crypto exchanges is being traced.')
                ]
            },
            {
                'title': 'Severe Domestic Assault, Dowry Coercion and Unlawful Confinement of Married Woman',
                'category': 'domestic_violence',
                'description': 'Immediate emergency distress: neighbor reporting sustained screaming, blunt trauma assaults, and persistent dowry harassment against a 26-year-old woman in apartment 1202. Resident mobile phone was confiscated by in-laws, and she has been locked in bedroom without meals for over 36 hours. Cries for emergency help overheard by neighboring families.',
                'incident_date': timezone.now() - timezone.timedelta(hours=10),
                'address': 'B-14/1202, Gokuldham Heights, Film City Road, Goregaon East, Mumbai, Maharashtra - 400063',
                'latitude': 19.1663,
                'longitude': 72.8732,
                'is_anonymous': True,
                'contact_email': '',
                'contact_phone': '',
                'reporter': None,
                'priority': 'critical',
                'department': departments['WOMEN-SAFETY'],
                'assigned_to': admin_users['admin2'],
                'status': 'investigating',
                'is_escalated': True,
                'escalation_reason': 'Active ongoing physical violence, domestic confinement, and confiscation of communication devices.',
                'tasks': [
                    ('Dispatch Women Safety Emergency Response Vehicle (Dial 1091) with local police station', True, staff_users['officer_sharma']),
                    ('Safeguard victim and transfer to District Hospital for medico-legal examination', True, staff_users['officer_sharma']),
                    ('File comprehensive complaint under Protection of Women from Domestic Violence Act 2005', False, admin_users['admin2']),
                    ('Appoint government legal aid counsel and safe shelter accommodation', False, None)
                ],
                'notes': [
                    (admin_users['admin2'], 'Emergency response unit safely intervened at 02:30 AM. Victim transported to trauma care center. Dindoshi Police Station has taken cognizance.')
                ]
            },
            {
                'title': 'Forced Child Labor and Physical Exploitation in Automobile Scrap & Gas Welding Garages',
                'category': 'child_abuse',
                'description': 'Four minors between the ages of 8 and 14 years engaged in hazardous industrial dismantling of heavy commercial truck chassis and oxygen-acetylene gas welding without protective eye goggles, respirators, or safety shoes. Children are made to work 12-hour shifts daily for ₹80/day and subjected to verbal and corporal punishment.',
                'incident_date': timezone.now() - timezone.timedelta(days=2, hours=3),
                'address': 'C-Block, Mayapuri Industrial Area Phase-1, Metal Yard 42, New Delhi - 110064',
                'latitude': 28.6369,
                'longitude': 77.1265,
                'is_anonymous': False,
                'contact_email': 'arjun.mehta@yahoo.co.in',
                'contact_phone': '+91 98200 11223',
                'reporter': citizen_users['arjun_mehta'],
                'priority': 'critical',
                'department': departments['NCPCR-CHILD'],
                'assigned_to': admin_users['admin2'],
                'status': 'under_review',
                'is_escalated': True,
                'escalation_reason': 'Severe hazardous child labor violating Child Labour (Prohibition & Regulation) Act and POCSO guidelines.',
                'tasks': [
                    ('Coordinate joint rescue operation with Sub-Divisional Magistrate (SDM Patel Nagar)', True, staff_users['officer_sharma']),
                    ('Produce rescued children before Child Welfare Committee (CWC Nirmal Chhaya)', False, staff_users['officer_sharma']),
                    ('Seal premises and register FIR under Sections 75 & 79 Juvenile Justice Act', False, admin_users['admin2'])
                ],
                'notes': [
                    (admin_users['admin2'], 'SDM Patel Nagar notified. Joint enforcement task force scheduled for unannounced morning raid.')
                ]
            },
            {
                'title': 'Clandestine Distribution of Banned Synthetic MDMA & Prescription Narcotics near University Hub',
                'category': 'drug_trafficking',
                'description': 'Syndicate using makeshift pan shop and tea kiosks near academic hostels as discreet delivery points for commercial quantities of synthetic mephedrone, vape cartridges with THC derivatives, and scheduled H1 prescription drugs. Orders coordinated through burner Telegram accounts with QR code UPI cashouts.',
                'incident_date': timezone.now() - timezone.timedelta(days=4),
                'address': 'Near Chhatra Marg, Behind Arts Faculty, North Campus, University of Delhi, Delhi - 110007',
                'latitude': 28.6893,
                'longitude': 77.2091,
                'is_anonymous': True,
                'contact_email': '',
                'contact_phone': '',
                'reporter': None,
                'priority': 'high',
                'department': departments['CYBER-CELL'],
                'assigned_to': admin_users['admin1'],
                'status': 'submitted',
                'is_escalated': False,
                'tasks': [
                    ('Deploy plainclothes surveillance operatives around North Campus perimeter', False, staff_users['inspector_verma']),
                    ('Procure chemical test kit and obtain search authorization under NDPS Act 1985', False, admin_users['admin1'])
                ],
                'notes': []
            },
            {
                'title': 'Uncovered Deep Stormwater Drain and Collapsed Culvert on High-Density School Route',
                'category': 'other',
                'description': 'Deep 14-foot open municipal stormwater drain culvert with missing cast-iron manhole covers directly adjacent to primary school pedestrian crossing. Waterlogged during evening hours creating fatal hazard for young schoolchildren and elderly pedestrians.',
                'incident_date': timezone.now() - timezone.timedelta(days=6),
                'address': 'Opposite Kendriya Vidyalaya Gate 2, Salt Lake Sector 1, Bidhannagar, Kolkata, West Bengal - 700064',
                'latitude': 22.5867,
                'longitude': 88.4178,
                'is_anonymous': False,
                'contact_email': 'ananya.sen@gmail.com',
                'contact_phone': '+91 98300 44556',
                'reporter': citizen_users['ananya_sen'],
                'priority': 'high',
                'department': departments['MCD-CIVIC'],
                'assigned_to': admin_users['admin2'],
                'status': 'resolved',
                'is_escalated': False,
                'resolution_summary': 'Heavy-duty ductile iron (DI) lockable manhole covers installed. Reinforced concrete safety grating affixed across culvert mouth. LED road-level solar blinkers erected.',
                'tasks': [
                    ('Install emergency high-visibility barricading and solar flashing hazard beacons', True, staff_users['inspector_singh']),
                    ('Cast reinforced concrete manhole collar and lock DI cover', True, staff_users['inspector_singh']),
                    ('Conduct 3-kilometer safety audit of storm drain stretch across Sector 1', True, staff_users['inspector_singh'])
                ],
                'notes': [
                    (admin_users['admin2'], 'Site inspection completed on Day 3. Civil repair work inspected and certified safe by Zonal Assistant Engineer.')
                ]
            },
            {
                'title': 'Spurious & Expired Pediatric Cough Syrups Relabeled with Forged Holograms in Wholesale Market',
                'category': 'other',
                'description': 'Wholesale pharmacy distributor caught relabeling expired batches of pediatric paracetamol and anti-allergic syrups with forged manufacturing holograms and altered expiry stamps. Over 4,000 bottles already shipped to rural dispensaries across neighboring districts.',
                'incident_date': timezone.now() - timezone.timedelta(days=3),
                'address': 'Shop 12, Dawa Bazaar, Koti Medical Market, Sultan Bazar, Hyderabad, Telangana - 500095',
                'latitude': 17.3850,
                'longitude': 78.4867,
                'is_anonymous': False,
                'contact_email': 'kavita.reddy@gmail.com',
                'contact_phone': '+91 99490 88776',
                'reporter': citizen_users['kavita_reddy'],
                'priority': 'critical',
                'department': departments['CVC-VIGILANCE'],
                'assigned_to': admin_users['admin2'],
                'status': 'under_review',
                'is_escalated': True,
                'escalation_reason': 'Severe imminent threat to pediatric lives across rural government primary health centers.',
                'tasks': [
                    ('Dispatch Drug Inspector and seize entire warehouse inventory of batch No. DX-2024', True, staff_users['inspector_singh']),
                    ('Send seized syrup ampoules to Central Drugs Standard Control Organisation (CDSCO) lab', False, admin_users['admin2']),
                    ('Cancel wholesale drug license and lodge criminal FIR under Drugs and Cosmetics Act', False, admin_users['admin2'])
                ],
                'notes': [
                    (admin_users['admin2'], 'State Drug Control Administration alerted. Over 3,800 bottles seized from transit warehouses.')
                ]
            }
        ]

        for case_data in sample_cases:
            report = Report.objects.create(
                title=case_data['title'],
                category=case_data['category'],
                description=case_data['description'],
                incident_date=case_data['incident_date'],
                address=case_data['address'],
                latitude=case_data.get('latitude'),
                longitude=case_data.get('longitude'),
                is_anonymous=case_data['is_anonymous'],
                contact_email=case_data['contact_email'],
                contact_phone=case_data['contact_phone'],
                reporter=case_data['reporter'],
                priority=case_data['priority'],
                department=case_data['department'],
                assigned_to=case_data['assigned_to'],
                status=case_data['status'],
                is_escalated=case_data.get('is_escalated', False),
                escalation_reason=case_data.get('escalation_reason', ''),
                resolution_summary=case_data.get('resolution_summary', ''),
            )

            # Initial status history
            ReportStatusHistory.objects.create(
                report=report,
                previous_status='submitted',
                new_status=case_data['status'],
                changed_by=case_data['assigned_to'],
                notes=f'Triage and intake processed by {case_data["assigned_to"].get_full_name() or case_data["assigned_to"].username}.'
            )

            # Investigation Tasks
            for task_title, is_done, assigned_officer in case_data.get('tasks', []):
                InvestigationTask.objects.create(
                    report=report,
                    title=task_title,
                    is_completed=is_done,
                    assigned_to=assigned_officer or case_data['assigned_to'],
                    completed_by=assigned_officer if is_done else None,
                    completed_at=timezone.now() if is_done else None
                )

            # Review Notes
            for author_user, note_text in case_data.get('notes', []):
                ReviewNote.objects.create(
                    report=report,
                    author=author_user,
                    content=note_text
                )

            # Audit event for compliance
            AuditEvent.objects.create(
                user=case_data['assigned_to'],
                action='CASE_TRIAGE_SEEDED',
                resource_type='Report',
                resource_id=str(report.id),
                details=f'Case [{report.reference_id}] "{report.title[:45]}..." triaged to {report.department.code}.',
                ip_address='127.0.0.1'
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(sample_cases)} authentic Indian civic grievances and abuse complaints."))
        self.stdout.write(self.style.SUCCESS("All tasks, timelines, audit trails, and nodal departments synchronized."))
