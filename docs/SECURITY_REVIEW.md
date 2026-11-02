# redFlag: Security, Privacy & Production-Readiness Review

**Date:** October 2026  
**Auditor:** Senior Security Reviewer & Full-Stack Architect  
**Scope:** Architecture, Django Settings, Authorization Boundaries, Upload Handling, Privacy Controls  
**Deploy Check Status:** 0 Issues / 0 Warnings with production environment variables  

---

## 1. Threat Modeling & Vulnerability Remediation

| Threat / Risk Vector | Status in Original MERN | Resolution in redFlag Django | Verification Method |
| :--- | :--- | :--- | :--- |
| **Public Data Exposure (CVE-level)** | `GET /api/reports` dumped every report and complainant contact to anyone. | Eliminated raw public endpoint. Replaced with aggregate `/transparency/` metrics. Public lookup (`/reports/track/`) returns only high-level status timeline. | Automated tests in `test_security.py` & Playwright Journey A. |
| **Insecure Direct Object Reference (IDOR)** | No ownership checks. | Strict server-side object ownership in `report_detail` (`report.reporter == request.user or request.user.is_staff`). Violations trigger **HTTP 403 Forbidden**. | Automated test `test_cross_user_access_denied_403` & Playwright Journey C. |
| **Reference Code Enumeration** | 6-digit predictable sequence (`JX-XXXXXX`). | High-entropy, cryptographically random reference ID (`RF-YYYY-XXXXXX`) using `secrets.choice()` with unambiguous alphabet. | Model tests in `test_models.py`. |
| **Unauthenticated Staff Portal** | Fake client-side login posting to non-existent endpoint. | Built-in Django session auth with `is_staff` check. Non-staff attempting access to `/staff/` are immediately redirected. | Automated test `test_non_staff_cannot_access_review_queue` & Playwright Journey C. |
| **Unrestricted File Uploads** | No validation or storage isolation. | Strict extension allowlist (`.jpg`, `.jpeg`, `.png`, `.webp`, `.pdf`, `.mp4`), 5MB file size limit, and MIME signature check. Private storage partition with authenticated streaming download (`download_evidence`). | Form tests in `test_forms.py` & staff view test. |
| **CSRF & Injection Attacks** | No CSRF validation on Express API. | Django `CsrfViewMiddleware` enabled across all POST forms. Template auto-escaping enabled by default. ORM parameterized queries prevent SQL injection. | Automated test suite & Playwright form submissions. |
| **Malicious Accusations / Defamation** | Instant public broadcast of unverified allegations. | Reports held in triage queue (`submitted` status) until reviewed by verified staff. Raw text never published publicly. | Data model & workflow state machine. |

---

## 2. Django Security Configuration

### 2.1 Core Settings
- **`DEBUG` Flag:** Defaults to `True` for local development; switches to `False` via `DEBUG=False` environment variable in production.
- **`SECRET_KEY`:** Sourced strictly from environment variable `SECRET_KEY`. Throws warning if default development key is retained.
- **`ALLOWED_HOSTS`:** Sourced from environment variable `ALLOWED_HOSTS`.
- **`CSRF_TRUSTED_ORIGINS`:** Configurable via environment variable for production HTTPS reverse proxies.

### 2.2 Cookie & Transport Security
In production (`DEBUG=False`):
- `SESSION_COOKIE_HTTPONLY = True` (Prevents client-side script access to session tokens)
- `CSRF_COOKIE_HTTPONLY = True`
- `SECURE_BROWSER_XSS_FILTER = True`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = 'DENY'` (Clickjacking prevention)
- `SECURE_SSL_REDIRECT = True` (Configurable via `SECURE_SSL_REDIRECT=True`)
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_HSTS_SECONDS = 31536000` (Optional HSTS header support)

---

## 3. Deployment Checklist for Production

When deploying redFlag to production behind Nginx/Caddy and Gunicorn/Uvicorn:

1. **Environment Variables:**
   ```env
   DEBUG=False
   SECRET_KEY=generate-a-50-character-cryptographic-random-string
   ALLOWED_HOSTS=redflag.yourdomain.org
   CSRF_TRUSTED_ORIGINS=https://redflag.yourdomain.org
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   SECURE_HSTS_SECONDS=31536000
   ```
2. **Static & Media Collection:**
   ```bash
   python manage.py collectstatic --noinput
   ```
3. **Database Migrations:**
   ```bash
   python manage.py migrate
   ```
4. **Media Storage Security:**
   - Ensure the `media/evidence/` directory is NOT served directly by Nginx as a static directory.
   - All evidence downloads must pass through the Django view `apps.reviews.views.download_evidence` to enforce staff credentials.
5. **Database Strategy:**
   - For local development and low-concurrency deployments, SQLite is fully functional and supported.
   - For high-volume multi-process production concurrency, transition to PostgreSQL by updating `DATABASES['default']` in `config/settings.py` (all models use portable Django ORM constructs without SQLite-specific locks).

