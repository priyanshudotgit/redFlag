# redFlag: UX Plan & User Journeys

**Project:** redFlag — Civic Abuse & Grievance Reporting System  
**Document:** `docs/UX_PLAN.md`  

---

## 1. Information Architecture & Navigation

```text
redFlag Global Navigation
│
├── Public Navigation
│   ├── Home (/) ── Overview, mission, core reporting portal, civic transparency stats
│   ├── How It Works (/how-it-works/) ── Complete reporting workflow & verification guide
│   ├── Helplines (/helpline/) ── Emergency contact numbers & immediate response agencies
│   ├── Civic Transparency (/transparency/) ── Anonymized aggregate metrics & outcomes
│   ├── File a Report (/reports/new/) ── Secure incident submission form (Primary CTA)
│   └── Track Status (/reports/track/) ── Lookup progress with unique reference ID
│
├── Reporter Account Flow
│   ├── Register (/accounts/register/) ── Optional citizen account creation
│   ├── Sign In (/accounts/login/) ── Unified sign-in for citizens and staff
│   ├── Dashboard (/dashboard/) ── Private list of user's submitted reports
│   └── Logout (/accounts/logout/) ── Secure session termination
│
└── Staff Review Portal (Restricted: `is_staff=True`)
    ├── Review Queue (/staff/queue/) ── Filterable, sortable list of all submitted reports
    ├── Report Detail (/staff/reports/<id>/) ── Full case view, evidence, notes & status actions
    ├── Status Transition (/staff/reports/<id>/status/) ── State change with audit reason
    ├── Internal Notes (/staff/reports/<id>/notes/) ── Private investigator case notes
    └── Evidence Access (/staff/evidence/<id>/) ── Authenticated file download view
```

---

## 2. Core User Journeys

### Journey 1: The Anonymous / First-Time Reporter
1. **Discovery:** User arrives at the redFlag landing page. Reads the clear, sober explanation of how reporting works and what anonymity genuinely means.
2. **Initiation:** Clicks the prominent "Submit an Incident Report" button.
3. **Form Completion:**
   - Enters incident title and selects a validated category (Child Abuse, Domestic Violence, Fraud/Corruption, Harassment, Robbery, etc.).
   - Specifies incident date and time (validated on server to disallow future dates).
   - Enters location address (optionally using GPS coordinates for precision).
   - Writes a detailed incident statement.
   - Attaches optional supporting evidence (image or document, validated for file type and capped at 5MB).
   - Chooses privacy setting: "Remain Anonymous" or "Provide Contact Details".
4. **Submission & Acknowledgement:**
   - Server processes submission inside a database transaction.
   - Generates an immutable, non-sequential reference code (e.g. `RF-2026-89412A`).
   - Displays Acknowledgement screen with the reference code, a one-click copy button, and a clear explanation of how to track resolution.
5. **Follow-Up:** User visits `/reports/track/`, enters reference code, and sees real-time status (`Submitted`, `Under Review`, `Investigating`, `Resolved`) and status timestamp history without exposing their identity.

---

### Journey 2: The Registered Citizen Reporter
1. **Account Registration / Login:** Reporter creates an account with email and secure password.
2. **Authenticated Submission:** Fills the report form while logged in. The report is securely tied to `request.user` while retaining the option to mask contact details from public or external views.
3. **Personal Dashboard:**
   - Reporter accesses `/dashboard/` to view their active and resolved cases.
   - Can inspect timeline transitions and official updates.
   - Object-level security guarantees they cannot access or view reports belonging to other reporters.

---

### Journey 3: The Staff Reviewer / Departmental Officer
1. **Secure Login:** Staff member logs in via `/accounts/login/`.
2. **Queue Management:**
   - Directed to `/staff/queue/`.
   - Filters reports by category, status (`Submitted`, `Under Review`, `Investigating`, `Resolved`, `Closed`), and date range.
   - Searches by reference code or location keyword.
3. **Case Review & Investigation:**
   - Clicks into a report to view complete details.
   - Downloads and verifies uploaded evidence securely through authenticated view.
   - Appends private investigation notes visible only to staff.
4. **Status Progression:**
   - Transitions status (e.g. `Submitted` -> `Under Review` -> `Investigating` -> `Resolved`).
   - Submits a required public resolution note or closing rationale.
   - Transition is logged into `ReportStatusHistory` with the staff member's user ID and timestamp.

---

## 3. Screen Specifications & States

| Screen | Primary Purpose | Key States Handled |
| :--- | :--- | :--- |
| **Landing (`/`)** | Establish trust, explain mission, guide actions | Normal, mobile layout, reduced-motion |
| **How It Works (`/how-it-works/`)** | Step-by-step reporting and review protocol | Static educational reading |
| **Helplines (`/helpline/`)** | Immediate emergency and crisis contacts | Click-to-call links, emergency banner |
| **Transparency (`/transparency/`)** | Aggregate civic resolution statistics | Live calculated totals, empty state |
| **Submit Report (`/reports/new/`)** | Guided incident reporting form | Pristine, validating, field errors, error summary, file attached, loading spinner |
| **Acknowledgement (`/reports/ack/`)** | Confirmation with reference code | Generated code, copy-to-clipboard, track CTA |
| **Track Status (`/reports/track/`)** | Look up report by reference code | Search input, not found error, timeline view |
| **User Dashboard (`/dashboard/`)** | View user's submitted reports | Empty state (no reports), active list, status badges |
| **Staff Queue (`/staff/queue/`)** | Manage review backlog | Filtered list, zero matches empty state, pagination |
| **Staff Detail (`/staff/reports/<id>/`)** | Review evidence, change status, add notes | Status form, notes form, evidence viewer, audit history |
| **Error 403 / 404 / 500** | Friendly, safe, unrevealing error pages | Clear message, link back to home |

---

## 4. Key Interaction States

1. **Default / Pristine:** Clean inputs, clear placeholder text, neutral borders.
2. **Focus:** `2px solid #0F172A` outline with `2px` offset (`focus:ring-2 focus:ring-slate-900 focus:outline-none`).
3. **Validation Error:** Red border (`border-red-600`), error message icon with text below input, and summary anchor list at top.
4. **Loading / Processing:** Button disabled, opacity 75%, spinner indicator, button text changes to *"Submitting..."* or *"Processing..."*.
5. **Feedback / Success:** Django message toast at top of viewport with auto-dismiss or manual close button.

