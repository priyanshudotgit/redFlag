# redFlag: Public Abuse & Civic Grievance Reporting System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-v3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-43%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**redFlag** is an independent, secure civic accountability platform engineered to empower citizens and whistleblowers to report public abuse of power, corruption, severe civic grievances, and public safety threats under verified privacy controls.

Formerly a prototype MERN-based application (`JusticeX`), redFlag has been completely rebuilt as an accessible, server-rendered Django application with SQLite and Tailwind CSS, eliminating critical data leakage vulnerabilities and establishing a sober, trustworthy civic interface. It includes an extensive **Executive Command Center & Multi-Module Admin Suite** designed for departmental intake, whistleblower verification, forensic evidence chain-of-custody, and inter-agency dispatch.

---

## Table of Contents
1. [Core Features](#core-features)
2. [Executive Command Center & Admin Platform](#executive-command-center--admin-platform)
3. [Technology Stack](#technology-stack)
4. [Architecture & Security Principles](#architecture--security-principles)
5. [Prerequisites](#prerequisites)
6. [Getting Started (Local Development)](#getting-started-local-development)
7. [Compiled CSS Workflow](#compiled-css-workflow)
8. [Running Tests](#running-tests)
9. [Test Accounts & Demo Data](#test-accounts--demo-data)
10. [Interface Previews](#interface-previews)
11. [Documentation Index](#documentation-index)
12. [License](#license)

---

## Core Features

- **Incident Filing Protocol:** Guided report submission supporting 9 civic categories (Child Abuse, Domestic Violence, Bribery/Corruption, Cyber Harassment, Drug Trafficking, etc.), incident timestamps, occurrence addresses, and auto-detected GPS coordinates.
- **Genuine Privacy & Anonymity:** When "Remain Anonymous" is checked, contact phone numbers and emails are sanitized on the server before database persistence. No tracking cookies or mandatory accounts required.
- **Cryptographic Tracking Reference:** Non-sequential, high-entropy reference codes (e.g. `RF-2026-YGRLF3`) allow reporters to monitor investigation milestones on `/reports/track/` without exposing personal identities.
- **Restricted Supporting Evidence:** Secure file upload support (JPG, PNG, WEBP, PDF, MP4 capped at 5MB) stored in private partitions outside the web root, accessible strictly to authorized departmental reviewers via streaming downloads.
- **Citizen Case Dashboard:** Optional authenticated citizen portal (`/dashboard/`) displaying an organized summary of personal submissions with object-level permission enforcement.
- **Civic Transparency Ledger:** Aggregate, non-defamatory resolution statistics (`/transparency/`) demonstrating departmental accountability without publishing unverified allegations.
- **Crisis Helpline Directory:** Rapid distress contact directory with click-to-call links for emergency services (112, Childline 1098, Women's Helpline 1091, Cyber Crime 1930).

---

## Executive Command Center & Admin Platform

The platform includes a comprehensive, multi-module administrative operations suite accessible to authorized personnel (`/staff/`):

### 1. Executive Intelligence Command Center (`/staff/`)
- Live operational KPIs (Total complaints, immediate triage intake, under review, formal inquiries ongoing, resolution rate).
- Urgent Incidents & Director Escalation table for rapid executive intervention.
- Breakdown of grievance typologies and active departmental workloads against target response SLAs.
- Real-time audit activity feed and chronological workflow progression stream.

### 2. Advanced Case Management & Triage Ledger (`/staff/queue/`)
- Multi-attribute search and filtering (keyword search, category, status, priority, filing type, department, assigned officer, escalation toggle).
- Batch/bulk operations: Mark selected under review, dispatch to formal investigation, escalate to critical priority, or export selected cases to CSV.
- Rich tabular ledger displaying Reference ID, incident title, who filed it (verified citizen vs protected whistleblower badge), priority severity, nodal department, assigned officer, status, and filing age.

### 3. Investigation Workbench & Filer Dossier (`/staff/reports/<id>/`)
- **Who Filed This Case (Filer Dossier):**
  - **Identified Citizens:** Displays verified name, username, official email, phone, residential address, reputation score meter, trust tier badge, and lifetime filing history with direct case links.
  - **Anonymous Whistleblowers:** Protected whistleblower shield card; personal identities intentionally suppressed to protect from retribution; records intake timestamps and optional secure contact channels.
- **Grievance Narrative & GPS Coordinates:** Full complainant statement, physical location, and Google Maps pin integration.
- **Forensic Evidence Vault & SHA-256 Registry:** Central evidence registry tracking file sizes, upload timestamps, citizen vs departmental tags, and automated 64-character SHA-256 cryptographic hashes for chain-of-custody integrity.
- **Investigation Tasks Checklist:** Interactive checklist for investigators to assign and complete field tasks (site inspection, witness interviews, CCTV retrieval, forensic tests).
- **Workflow State Machine:** Permitted status transitions (`submitted` → `under_review` → `investigating` → `resolved` / `closed`) with mandatory transition rationales and formal resolution summaries.
- **Department & Officer Dispatch:** Reassign cases across departments and assign lead investigating officers with dispatch instructions.
- **Severity & Escalation Panel:** Set priority levels (Critical, High, Medium, Low) and trigger director supervisory escalation with justification.
- **Confidential Staff Notebook:** Staff-only internal investigation notes with priority tagging (`normal`, `important`, `urgent`) and pinning.

### 4. Printable Official Incident Case Dossier (`/staff/reports/<id>/dossier/`)
- Formal, print-ready case dossier (`@media print` optimized) for legal transmission, court proceedings, or physical departmental archives.
- Includes incident metadata, complainant record, evidence ledger with SHA-256 checksums, chronological chain-of-custody logs, and official sign-off lines for Investigating Officer, Department Head, and Supervisory Director.

### 5. Inter-Agency Routing Matrix & Nodal Departments (`/staff/departments/`)
- Directory of municipal departments, police liaisons, and statutory watchdogs.
- Configurable response SLAs (in hours), contact coordinates, active caseload tallies, and new department registration.

### 6. Citizen Reporters Directory & Trust Calibration (`/staff/reporters/`)
- Directory of registered citizen filers with lifetime filing counts and resolution rates.
- Detailed citizen profile view (`/staff/reporters/<id>/`) allowing staff to calibrate trust tiers (`standard`, `verified`, `trusted`, `restricted`) and adjust reputation scores.

### 7. Staff Officers Caseload Directory (`/staff/officers/`)
- Workload balancing dashboard showing all staff officers, administrative roles, active ongoing cases, and lifetime assignments with one-click queue filters.

### 8. Immutable Security Audit Trail (`/staff/audit-logs/`)
- Searchable chronological ledger capturing every administrative action (`STATUS_TRANSITION`, `PRIORITY_UPDATED`, `OFFICIAL_EVIDENCE_ATTACHED`, `DATA_EXPORT_GENERATED`, etc.) with user identity, resource target, IP address, and operational details.

### 9. Intelligence & Data Export Hub (`/staff/export/`)
- Custom dataset extraction engine allowing staff to filter by status, category, and priority.
- One-click export to **Tabular CSV** (for spreadsheets) or **Structured JSON** (for external systems/APIs) with automated whistleblower identity sanitization.

### 10. System Bulletins & Safety Advisories (`/staff/announcements/`)
- Departmental broadcast manager for publishing public alerts, seasonal fraud warnings, or staff operational directives with active/archive toggle controls.

---

## Technology Stack

- **Backend:** Python 3.12, Django 6.1 (Standard ORM, sessions, CSRF protection, ModelForms).
- **Database:** SQLite (local persistent database, zero external database service required).
- **Frontend:** Server-rendered Django templates, HTML5 semantic landmarks, vanilla JavaScript.
- **Styling:** Compiled Tailwind CSS v3.4 (Production build with zero CDN dependencies).
- **Design System:** Dealt `editorial-report` art direction via Taste Skill, Literata & Inter typography, Gov.uk accessible form standards.
- **Testing:** Django Test Runner (43 automated unit, form, security, and admin suite tests) & Playwright CLI browser automation.

---

## Architecture & Security Principles

1. **Private by Default:** Raw complaint text, witness identities, and contact phone numbers are never broadcast to open public feeds.
2. **Strict Object Ownership:** Citizens can access only their own cases; cross-user URL tampering is denied with **HTTP 403 Forbidden**.
3. **Encapsulated Evidence:** Media files are never directly reachable via public web server URLs; downloads stream through authenticated Django views enforcing `is_staff` privileges.
4. **Anti-Enumeration Keys:** 6-character cryptographic tokens prevent sequential ID scraping attacks.
5. **Immutable Audit Trail:** All administrative operations generate persistent `AuditEvent` records with IP and timestamp metadata.
6. **Zero Deceptive Branding:** Removed unauthorized state crests, fake ISO certifications, and fabricated departmental claims from the legacy prototype in favor of an authentic, credible civic identity.

---

## Prerequisites

- **Python:** 3.12+
- **Node.js:** v18+ (Required only for compiling Tailwind CSS)
- **Git**

---

## Getting Started (Local Development)

### 1. Clone the repository
```bash
git clone https://github.com/Vegapunk-debug/public-abuse-reporting-system-justicex.git
cd public-abuse-reporting-system-justicex/redFlag
```

### 2. Set up Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template configuration:
```bash
cp .env.example .env
```
Default `.env` settings are pre-configured for instant local development.

### 4. Apply Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Test Accounts & Sample Data
Populate the database with test accounts and sample incident cases across all categories:
```bash
python manage.py seed_demo_data
```

### 6. Start the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Visit the application in your browser at `http://127.0.0.1:8000/`.

---

## Compiled CSS Workflow

The project uses a reproducible Tailwind CSS build pipeline. The compiled stylesheet resides at `static/css/styles.css`.

- **Compile Minified Production CSS:**
  ```bash
  npm run build:css
  ```
- **Watch for Template Changes during Development:**
  ```bash
  npm run watch:css
  ```

---

## Running Tests

### Automated Django Test Suite
Execute all 43 automated unit, form, security, and administrative suite tests:
```bash
python manage.py test
```

### Run Specific Test Modules
```bash
# Admin Platform & Command Center tests (18 tests)
python manage.py test tests.test_admin_suite

# Security and IDOR tests
python manage.py test tests.test_security

# Review workflow tests
python manage.py test tests.test_reviews
```

### Deployment Configuration Check
Verify production readiness settings:
```bash
python manage.py check --deploy
```

---

## Test Accounts & Demo Data

The `seed_demo_data` command generates pre-configured test credentials for local evaluation:

| Role | Username | Password | Email | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Supervisory Director** | `director_vance` | `Password123!` | `director@redflag.internal` | Full access to Command Center, triage queue, case escalations, staff directory, audit trail |
| **Investigating Staff** | `officer_smith` | `Password123!` | `officer@redflag.internal` | Access to triage queue, case workbench, task checklist, official evidence uploads |
| **Forensic Investigator** | `investigator_lee` | `Password123!` | `lee@redflag.internal` | Access to case workbench, evidence hashes, departmental notes |
| **Intake Officer** | `officer_patel` | `Password123!` | `patel@redflag.internal` | Access to incoming triage backlog |
| **Verified Citizen** | `jane_citizen` | `Password123!` | `jane@example.org` | Access to `/dashboard/` to view personal submissions; high trust score |
| **Witness Reporter** | `alex_witness` | `Password123!` | `alex@example.org` | Access to citizen dashboard |
| **Restricted User** | `spurious_tester` | `Password123!` | `spurious@example.org` | Demo account flagged for frivolous filings |

---

## Interface Previews

Screenshots captured during Playwright browser automation tests are stored in `test_screenshots/`:

### Citizen Platform
| Screen | Description |
| :--- | :--- |
| `01_home_desktop.png` | Landing page hero and live civic ledger |
| `04_report_form.png` | Incident filing form with privacy protocol |
| `05_report_ack.png` | Official acknowledgement receipt with reference code |
| `06_track_report.png` | Public case milestone progression timeline |
| `08_citizen_dashboard.png` | Authenticated citizen dashboard |
| `10_access_denied_403.png` | Server-enforced IDOR security boundary |
| `14_mobile_home.png` | Responsive mobile viewport layout |
| `15_mobile_nav_open.png` | Accessible mobile navigation drawer |

### Admin Platform & Command Center
| Screen | Description |
| :--- | :--- |
| `admin_01_command_center.png` | Executive Intelligence Command Center with KPIs & live audit feeds |
| `admin_02_cases_queue.png` | Advanced Case Management queue with multi-filtering & bulk actions |
| `admin_03_case_workbench_anonymous.png` | Case workbench with Anonymous Whistleblower Protection Shield |
| `admin_04_case_workbench_identified.png` | Case workbench with Verified Citizen Dossier, SHA-256 evidence vault, checklist |
| `admin_05_printable_case_dossier.png` | Printable official case dossier formatted for legal & departmental archive |
| `admin_06_departments.png` | Nodal Departments Directory & response SLA configuration |
| `admin_07_citizen_reporters.png` | Citizen Reporters Directory with trust verification ratings |
| `admin_08_officers_workload.png` | Investigating Officers workload distribution directory |
| `admin_09_audit_trail.png` | Immutable system security audit trail and activity log |
| `admin_10_export_hub.png` | Intelligence & Data Export Hub for custom CSV and JSON datasets |
| `admin_11_safety_bulletins.png` | System Bulletins & Public Safety Advisories broadcast manager |

---

## Documentation Index

Detailed architectural blueprints and audits are available in `docs/`:

- [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md) — Comprehensive technical inventory of the legacy MERN codebase and migration mapping.
- [`DESIGN.md`](DESIGN.md) — Complete design system specifications, color tokens, typography scales, and component guidelines.
- [`docs/UX_PLAN.md`](docs/UX_PLAN.md) — Information architecture, user journeys, and interaction states.
- [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) — Entity-relationship diagram, field constraints, state machine transitions, and privacy rules.
- [`docs/UI_AUDIT.md`](docs/UI_AUDIT.md) — Vercel Web Interface Guidelines audit and accessibility checklist.
- [`docs/TESTING.md`](docs/TESTING.md) — Automated test results and end-to-end Playwright browser journeys.
- [`docs/SECURITY_REVIEW.md`](docs/SECURITY_REVIEW.md) — Threat modeling, CVE remediations, and production deployment checklist.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
