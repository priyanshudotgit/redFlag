# redFlag: Quality Assurance, Automated Tests & Browser Journey Report

**Date:** October 2026  
**Auditor / QA Lead:** Senior QA Engineer & Django Architect  
**Test Suite:** Django Test Runner (`tests/`), Playwright CLI Browser Automation  
**Results:** 43/43 Automated Tests Passing (100%), 6/6 Browser Journeys Validated  

---

## 1. Automated Test Suite Summary

The automated test suite evaluates model validation, form edge cases, security ownership checks, CSRF and session handling, state machine transitions, and the entire administrative operations suite.

### Test Execution Command
```bash
python manage.py test
```

### Test Suite Matrix
| Test File | Target Domain | Assertions Checked | Status |
| :--- | :--- | :--- | :--- |
| `tests/test_models.py` | Model integrity & custom logic | Reference ID format, future date rejection, evidence size formatting, badge CSS mapping, status history creation, audit logging | **PASS** (5 tests) |
| `tests/test_forms.py` | Form validation & sanitization | Valid report submissions, future date rejection, malicious `.sh` upload rejection, >5MB file rejection, valid state machine choices, password confirmation matching | **PASS** (6 tests) |
| `tests/test_views.py` | Public & reporter workflows | HTTP 200 for all public views, report filing POST & redirect to receipt, tracking view with valid ID, error message for non-existent reference | **PASS** (4 tests) |
| `tests/test_security.py` | Authorization boundaries | User A can view own report, User B accessing User A report yields **HTTP 403**, unauthenticated user redirected to login, non-staff blocked from queue, staff granted access, anonymous submission strips contact details | **PASS** (6 tests) |
| `tests/test_reviews.py` | Staff moderation & workflow | Valid state transition updates report and status history, staff can append internal confidential note, civilians cannot trigger state machine transitions | **PASS** (4 tests) |
| `tests/test_admin_suite.py` | Executive Command Center & Admin Operations | Restricted access on all 9 admin endpoints, live KPI metrics context, anonymous vs identified filer dossier filtering, bulk case actions with audit logging, status transition with resolution summary, officer & department dispatch, priority severity & director escalation, checklist task addition and completion toggling, official evidence upload with SHA-256 hash generation, printable case dossier generation, department creation and response SLA, citizen trust status calibration and reputation score adjustment, officer workload directory, audit trail search, CSV and JSON data export streaming, system bulletin broadcast and toggle | **PASS** (18 tests) |

**Total:** 43 passed in 63.588s. Zero failures, zero errors.

---

## 2. Playwright CLI Browser Journeys

Real-browser interactions were executed against the active Django server (`http://127.0.0.1:8000/`) using Playwright CLI (Chromium).

### Journey A: Public Visitor Navigation
- **Actions:**
  1. Loaded `http://127.0.0.1:8000/` (Home).
  2. Verified navigation to `/how-it-works/`, `/helpline/`, and `/transparency/`.
  3. Confirmed that no individual raw accusations or personal telephone/email records are displayed on public pages.
- **Result:** **PASSED**.
- **Screenshots:**
  - `01_home_desktop.png` (Landing page)
  - `02_how_it_works.png` (Verification protocol)
  - `03_transparency.png` (Civic transparency ledger)

### Journey B: Incident Report Submission & Acknowledgement
- **Actions:**
  1. Opened `/reports/new/`.
  2. Submitted an empty form to test validation. Verified that the Gov.uk-style accessible error summary container rendered with anchor links to missing fields.
  3. Filled valid fictional incident data (*"Discharge of Unfiltered Chemical Waste near Sector 9 Drainage"*).
  4. Checked *"Protect My Identity (Remain Completely Anonymous)"*.
  5. Submitted the form. Verified database transaction commit and clean redirect to `/reports/ack/RF-2026-YGRLF3/`.
  6. Tested the public tracking interface (`/reports/track/?reference_id=RF-2026-YGRLF3`), verifying that the status (*"Submitted"*) and intake milestone rendered accurately without exposing reporter details.
- **Result:** **PASSED**.
- **Screenshots:**
  - `04_report_form.png` (Filing interface)
  - `05_report_ack.png` (Acknowledgement receipt with copyable ID)
  - `06_track_report.png` (Public case milestone timeline)

### Journey C: Authenticated Citizen Reporter
- **Actions:**
  1. Navigated to `/accounts/login/` and authenticated as `jane_citizen`.
  2. Verified landing on `/accounts/dashboard/`.
  3. Inspected user's submitted cases and clicked *"View Details"* on case `RF-2026-3CEYBT`. Verified complete statement, category, occurrence timestamp, and milestone history.
  4. **Negative Security Test:** Attempted to manually navigate to `http://127.0.0.1:8000/reports/view/RF-2026-YGRLF3/` (a case not owned by Jane).
  5. Verified immediate server-side denial with **HTTP 403 Forbidden** and custom error template.
- **Result:** **PASSED**.
- **Screenshots:**
  - `07_login_page.png` (Sign in screen)
  - `08_citizen_dashboard.png` (Citizen personal dashboard)
  - `09_case_detail_permitted.png` (Authorized case detail view)
  - `10_access_denied_403.png` (Security boundary enforcement)

### Journey D: Departmental Staff Reviewer
- **Actions:**
  1. Signed out of citizen account and signed in as `officer_smith` (`is_staff=True`).
  2. Accessed `/staff/queue/`. Filtered and reviewed incident backlog.
  3. Opened case review detail for case `RF-2026-YGRLF3`.
  4. Advanced status state machine from `submitted` to `under_review` with official transition notes (*"Case assigned to Inspector Patel for site inspection and water sample collection."*).
  5. Appended a confidential internal case note (*"Preliminary field report scheduled for Friday morning."*).
  6. Confirmed that internal case notes are badged *"Staff Only"* and logged with officer username and timestamp.
- **Result:** **PASSED**.
- **Screenshots:**
  - `11_staff_queue.png` (Staff review backlog)
  - `12_staff_detail_before.png` (Case review workspace)
  - `13_staff_detail_transition.png` (Status transition and confidential notes)

### Journey E: Responsive Fluidity & Mobile Navigation
- **Actions:**
  1. Resized viewport to mobile dimensions (`375x667` px).
  2. Tested home page layout, verifying absence of horizontal scroll or clipped elements.
  3. Toggled mobile hamburger menu, confirming accessible expansion (`aria-expanded="true"`) and full navigation access.
  4. Inspected reporting form inputs and buttons on mobile view.
- **Result:** **PASSED**.
- **Screenshots:**
  - `14_mobile_home.png` (Mobile landing viewport)
  - `15_mobile_nav_open.png` (Mobile navigation drawer)
  - `16_mobile_report_form.png` (Mobile form inputs and buttons)

### Journey F: Executive Command Center & Admin Operations Suite
- **Actions:**
  1. Authenticated as `director_vance` (`is_staff=True, is_superuser=True`).
  2. Navigated to `/staff/` (Executive Command Center). Inspected operational KPI cards, urgent attention backlog, nodal agency caseloads, and active security audit stream.
  3. Navigated to `/staff/queue/`. Tested multi-attribute filters (filing type = anonymous vs identified, priority severity, department dispatch).
  4. Inspected Case Workbench for an anonymous whistleblower (`/staff/reports/5/`), verifying that the Anonymous Whistleblower Protection Shield rendered and complainant identity was securely suppressed.
  5. Inspected Case Workbench for an identified citizen (`/staff/reports/9/`), verifying the Verified Citizen Dossier with full coordinates, reputation score, lifetime filings ledger, and action checklist.
  6. Generated the official printable case dossier (`/staff/reports/9/dossier/`), verifying court-ready formatting, forensic SHA-256 evidence register, and signature sign-offs.
  7. Inspected Nodal Departments Directory (`/staff/departments/`), Citizen Reporters Directory (`/staff/reporters/`), Staff Officers Directory (`/staff/officers/`), Security Audit Trail (`/staff/audit-logs/`), Intelligence Export Hub (`/staff/export/`), and Safety Bulletins (`/staff/announcements/`).
- **Result:** **PASSED**.
- **Screenshots:**
  - `admin_01_command_center.png` (Executive Command Center)
  - `admin_02_cases_queue.png` (Cases Triage Queue with bulk operations)
  - `admin_03_case_workbench_anonymous.png` (Whistleblower Protection Dossier)
  - `admin_04_case_workbench_identified.png` (Verified Citizen Dossier & Action Checklist)
  - `admin_05_printable_case_dossier.png` (Official Printable Incident Dossier)
  - `admin_06_departments.png` (Nodal Departments & Response SLAs)
  - `admin_07_citizen_reporters.png` (Citizen Reporters & Trust Tiers)
  - `admin_08_officers_workload.png` (Staff Officers Caseload Balancing)
  - `admin_09_audit_trail.png` (Immutable Security Audit Trail)
  - `admin_10_export_hub.png` (Intelligence & Data Export Hub)
  - `admin_11_safety_bulletins.png` (System Bulletins & Public Safety Advisories)

---

## 3. Visual Quality & Taste Skill Inspection
- **Editorial Tone:** Verified dignified, calm aesthetic matching `editorial-report` art direction. Removed all deceptive governmental emblems, fake ISO badges, and fabricated departmental claims.
- **Typography:** Literata display headers render with sharp gravitas; body copy in Inter provides crisp readability.
- **Contrast & Focus:** Focus outlines (`2px solid #0F172A`) render distinctly on Tab navigation.

