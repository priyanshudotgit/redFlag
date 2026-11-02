# redFlag: Project Audit & Migration Blueprint

**Date:** October 2026  
**Auditor:** Senior Full-Stack Engineer, Django Architect & Security Reviewer  
**Repository:** `redFlag` (formerly `JusticeX: Public Abuse Reporting System`)  
**Target Architecture:** Python 3.12 / Django 6.1 / SQLite / Server-Rendered Django Templates + Tailwind CSS / Playwright CLI  

---

## 1. Executive Summary

An exhaustive technical audit of the original MERN-based implementation (`JusticeX`) was conducted before modifying any code. The codebase was intended as a civic grievance and public abuse reporting tool, allowing individuals to submit incident reports either anonymously or with contact details, track status via a reference ID, and allow authorities to review reports.

However, the existing codebase contains critical security and privacy flaws, extensive discrepancies between documentation and actual implementation, fake marketing claims and unauthorized governmental watermarks, and broken or missing core architectural features (such as authentication and evidence storage).

This document serves as the foundational feature inventory and architectural migration map to transition **redFlag** into a secure, accessible, trustworthy, and fully functional Django application.

---

## 2. Feature Inventory

### 2.1 Working Functionality
- **Report Submission (`ReportForm.jsx` -> `POST /api/reports`):**
  - Accepts title, description, category, address, optional latitude/longitude, incident date and time, anonymous preference, and contact information.
  - Server generates a reference ID in the format `JX-XXXXXX` (6-digit integer), stores the document in MongoDB with default status `Pending`, and returns the ID.
- **Report Status Inquiry (`TrackStatus.jsx` -> `GET /api/reports/:id`):**
  - Accepts a reference ID and queries MongoDB.
  - Returns `reportId`, `title`, `status` (`Pending`, `Investigating`, `Resolved`, `Rejected`), and `updatedAt`.
- **Public Report Listing (`Reports.jsx` -> `GET /api/reports`):**
  - Fetches all reports in the database and renders them as cards.
  - Client-side category filtering using React state.
- **Client-Side Geolocation:**
  - Browser Geolocation API fetches latitude and longitude, followed by a reverse geocoding lookup via OpenStreetMap's Nominatim service to autofill the address field.
- **Static Informational Content:**
  - Informational pages for *How It Works*, *Emergency Helplines*, *About*, *Privacy Policy*, *Terms of Service*, *Disclaimer*, and *Data Protection*.

---

### 2.2 Incomplete or Broken Functionality
- **Evidence / Media Upload:**
  - The UI in `ReportForm.jsx` renders a file input accepting images and videos (`<input type="file" accept="image/*,video/*">`) and handles file removal in local React state.
  - **Fatal Defect:** `handleSubmit` never appends the file to `FormData` or the JSON payload. The server's `Report` model contains an unused `imageUrl` field (`default: 'no-photo.jpg'`), and `addReport` in `reportController.js` completely ignores uploads. No files were ever saved or processed.
- **Authentication & Staff Portal:**
  - `AdminLogin.jsx` displays a departmental login form posting to `http://localhost:5000/api/auth/login`.
  - **Fatal Defect:** The server listens on port 3000 (not 5000), has NO `/api/auth/login` route, NO User schema, and NO JWT verification middleware.
  - On simulated success, `AdminLogin.jsx` attempts to navigate to `/admin/dashboard`, which does not exist in `App.jsx` routes and has no associated component. The staff portal is completely non-existent.
- **Validation Deficiencies:**
  - Date validation exists only as a client-side JavaScript alert (`combinedDate > now`). The backend does not validate that dates are non-future, that string lengths conform to bounds, or that coordinates are valid floats.

---

### 2.3 Features Documented in README but Not Implemented
| Feature | Claim in README | Reality in Codebase |
| :--- | :--- | :--- |
| **User Authentication** | "JWT & Google OAuth 2.0 to protect user sessions" | Zero auth routes, zero user models, zero OAuth integrations. |
| **User Dashboard** | "Personalized dashboard where users can view history and status" | No dashboard route, no session management, no user-to-report relationships. |
| **Cloudinary Media** | "External Services: Cloudinary (Media)" | Zero Cloudinary packages installed or configured. |
| **Google Maps API** | "External Services: Google Maps API (Location)" | OpenStreetMap Nominatim was used instead of Google Maps API. |
| **Redux Toolkit** | "Frontend: Redux Toolkit" | Not installed or used; standard local state was used. |

---

### 2.4 Existing User Roles & Intended Permissions
- **MERN Reality:** No authorization logic or middleware existed. All database entries were publicly accessible via `GET /api/reports`.
- **Target Django Permission Model:**
  1. **Anonymous / Public Visitor:**
     - Can view public educational content (How It Works, Helplines, Legal/Privacy guidelines).
     - Can view aggregate, non-sensitive civic transparency statistics (no individual raw allegations).
     - Can submit a report (with or without an account).
     - Can check status of their report using their secure tracking code.
  2. **Authenticated Citizen (Optional Reporter Account):**
     - Can register and log in via Django session authentication.
     - Can submit reports linked to their account.
     - Can access a private dashboard showing only *their own* submitted reports and status timelines.
     - Object-level permission guarantees they cannot view or tamper with other users' reports.
  3. **Staff Reviewer / Departmental Officer:**
     - Belongs to Django `is_staff` group with review permissions.
     - Accesses a restricted Review Queue (`/staff/`).
     - Can view sensitive report details, verified evidence, and submit internal investigation notes (`ReviewNote`).
     - Can execute validated status transitions (`Submitted` -> `Under Review` -> `Investigating` -> `Resolved` / `Closed`).
     - Every action creates a timestamped `AuditEvent` / `StatusHistory` record.

---

### 2.5 Existing Database Entities & Relationships
- **Existing Mongoose Schema (`Report`):**
  - `reportId` (String, required, unique)
  - `title` (String, max 100)
  - `description` (String, max 5000)
  - `category` (Enum: Child Abuse, Drug Activity, Domestic Violence, Sexual Harassment, Human Trafficking, Cyber Bullying, Robbery, Other)
  - `location` (GeoJSON Point: `coordinates` [lng, lat], `address` String)
  - `imageUrl` (String)
  - `contact` (String)
  - `anonymous` (Boolean)
  - `incidentDate` (Date)
  - `status` (Enum: Pending, Investigating, Resolved, Rejected)
  - `createdAt` (Date)
- **Deficiencies:** Single isolated entity. No User foreign key, no Evidence model, no audit log, no staff notes.

---

### 2.6 External Services & Configuration Requirements
- **MERN Services:** Node.js, Express, MongoDB Atlas, OpenStreetMap Nominatim reverse geocoding API, external hotlinked images.
- **Django Replacement Strategy:**
  - Standard Python 3.12 + Django 6.1 stack.
  - Persistent SQLite database (local file excluded from Git).
  - Native Django static & media file handling with strict access control on uploaded evidence.
  - Zero external database dependencies required for development and testing.

---

### 2.7 UI and Accessibility Deficiencies
1. **Misleading Institutional Styling:**
   - Hotlinks the National Emblem of India directly from Wikimedia Commons as watermarks and headers.
   - Fabricates institutional claims: *"Ministry of Public Safety • Govt. of India"*, *"ISO-27001 Certified"*, *"92.4% Case Clearance"*, *"54 Units"*.
   - These deceptive patterns violate civic tech trust and will be replaced with an original, sober, and credible **redFlag** visual identity.
2. **Accessibility Barriers:**
   - Missing explicit `<label for="...">` associations on several form inputs.
   - Auto-rotating hero slider without pause controls or `prefers-reduced-motion` compliance.
   - Insufficient contrast ratios in muted text (`text-slate-400` on light grey backgrounds).
   - Incomplete keyboard navigation with missing `:focus-visible` styling.
   - Use of raw emoji (`⚠️`) instead of semantic icons with accessible screen-reader labels.
   - Mobile viewport regressions with fixed overlay buttons obstructing form submit buttons.

---

### 2.8 Security and Privacy Vulnerabilities (Critical Severity)
1. **Unrestricted Public Data Exposure (CVE-level flaw):**
   - In `reportController.js`, `GET /api/reports` returns all database records with zero authentication.
   - `Reports.jsx` displayed every complainant's unmasked contact details (phone number/email) if they did not tick anonymous.
   - Anyone could scrape sensitive allegations, names, locations, and contact details.
2. **Defamation & Unverified Accusations:**
   - Any anonymous visitor could submit unverified criminal accusations against named individuals and have them immediately published to the public internet.
3. **Predictable Reference ID Enumeration:**
   - IDs are generated as `JX-` + 6 random digits (`Math.floor(100000 + Math.random() * 900000)`). An attacker can easily enumerate all 900,000 possibilities to harvest statuses and titles.
4. **Unvalidated Uploads & CSRF Exposure:**
   - No CSRF token validation existed on the Express API.
   - No server-side file type, MIME signature, or size validation.

---

### 2.9 Decisions: Preserve, Improve, Simplify, Exclude

| Feature | Disposition | Architectural Rationale |
| :--- | :--- | :--- |
| **Incident Reporting Workflow** | **Preserve & Improve** | Retain title, category, description, occurrence date/time, and address. Add robust server-side validation, anti-tamper tracking token, and genuine file attachments. |
| **Evidence Uploads** | **Implement Securely** | Implement Django `Evidence` model with size caps (5MB max), strict extension and magic-byte validation, private filesystem storage, and authenticated staff access. |
| **Status Tracking** | **Preserve & Improve** | Retain status tracking by reference ID; add high-entropy UUID tracking tokens or access codes to eliminate enumeration attacks. |
| **Authentication & Sessions** | **Improve & Implement** | Use standard Django `django.contrib.auth` sessions. Build registration, login, user dashboard, and staff review portal. |
| **Public Grievance Wall** | **Exclude (Privacy)** | Do NOT publish unverified personal allegations to the public. Replace with an aggregate civic transparency overview (e.g. total reports filed, resolution rates, categories handled). |
| **Fake Government Badges** | **Exclude (Integrity)** | Remove unauthorized emblems, fake ISO claims, and fabricated agency statistics. Build an authentic, dignified redFlag civic design. |
| **MERN Architecture** | **Exclude (Migration)** | Replace React, Vite, Express, and MongoDB with server-rendered Django templates and SQLite. |

---

## 3. Route & Page Migration Map

| Original Frontend Route | Original Backend API | Proposed Django Route | Django View Name | Access Rule |
| :--- | :--- | :--- | :--- | :--- |
| `/` | N/A | `/` | `public:home` | Public |
| `/how-it-works` | N/A | `/how-it-works/` | `public:how_it_works` | Public |
| `/helpline` | N/A | `/helpline/` | `public:helpline` | Public |
| `/privacy-policy` | N/A | `/privacy/` | `public:privacy` | Public |
| `/terms-of-service` | N/A | `/terms/` | `public:terms` | Public |
| `/report` | `POST /api/reports` | `/reports/new/` | `reports:submit` | Public / Reporter |
| `/report` (Ack) | Return JX-ID | `/reports/acknowledgement/<ref>/` | `reports:acknowledgement` | Public / Reporter |
| `/track-status` | `GET /api/reports/:id` | `/reports/track/` | `reports:track` | Public / Reporter |
| `/reports` | `GET /api/reports` | `/transparency/` | `public:transparency` | Public (Aggregate Only) |
| (Missing) | N/A | `/dashboard/` | `accounts:dashboard` | Authenticated Reporter |
| `/admin-login` | `POST /api/auth/login` | `/accounts/login/` | `accounts:login` | Public |
| (Missing) | N/A | `/accounts/register/` | `accounts:register` | Public |
| (Missing) | N/A | `/accounts/logout/` | `accounts:logout` | Authenticated |
| (Missing) | N/A | `/staff/queue/` | `reviews:queue` | Staff Only |
| (Missing) | N/A | `/staff/reports/<pk>/` | `reviews:detail` | Staff Only |
| (Missing) | N/A | `/staff/reports/<pk>/status/` | `reviews:update_status` | Staff Only |
| (Missing) | N/A | `/staff/evidence/<pk>/download/` | `reviews:download_evidence`| Staff Only |
| N/A | N/A | Custom 403 / 404 / 500 | `errors:403`, etc. | Public |

---

## 4. Migration Plan & Sequence

1. **Phase 1 (Complete):** Repository audit, feature inventory, security analysis, and route mapping.
2. **Phase 2:** Product & UX design specification (`DESIGN.md`, `docs/UX_PLAN.md`) utilizing Taste Skill, Awesome Design MD reference, and Vercel guidelines.
3. **Phase 3:** Data modeling (`docs/DATA_MODEL.md`) defining Django models, SQLite database settings, status state-machine transitions, and privacy rules.
4. **Phase 4:** Django application build: virtual environment, Django settings, apps (`accounts`, `reports`, `reviews`, `public`), forms, views, auth, and permissions.
5. **Phase 5:** UI implementation with Tailwind CSS and Django templates: responsive layouts, accessible forms, status indicators, and staff dashboards.
6. **Phase 6:** Vercel Web Design Guidelines compliance review and UI fixes.
7. **Phase 7:** Automated testing (Django unit/integration tests) and end-to-end browser testing with Playwright CLI.
8. **Phase 8:** Production-readiness review (`docs/SECURITY_REVIEW.md`), deployment check, and security hardening.
9. **Phase 9:** Documentation (`README.md`, `.gitignore`, `.env.example`) and final cleanup.

