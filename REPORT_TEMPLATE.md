# Penetration Test Report — FakeCompany Portal

> **How to use this template:** Copy into your thesis / lab report document. Replace all `[bracketed]` placeholders with your own data, screenshots, and observations. Delete instructional notes (lines starting with `>`) before submission.

---

## Document Control

| Field | Value |
|-------|-------|
| **Report title** | Web Application Penetration Test — FakeCompany Internal Portal |
| **Author** | `[Your Name]` |
| **Institution / Course** | `[University, Program, Course Name]` |
| **Date** | `[DD Month YYYY]` |
| **Version** | `1.0` |
| **Classification** | Confidential — Educational Use Only |

---

## 1. Executive Summary

`[Write 1–2 paragraphs summarizing the engagement.]`

A black-box / gray-box web application penetration test was performed against the **FakeCompany Internal Portal** — a deliberately vulnerable corporate HR application deployed in an isolated laboratory environment. Testing followed the **OWASP Web Security Testing Guide (WSTG)** methodology and was conducted primarily with **Burp Suite Community Edition** and manual exploitation techniques.

**Key results:**

| Metric | Value |
|--------|-------|
| Total findings | `[e.g. 5]` |
| Critical | `[0]` |
| High | `[e.g. 2]` |
| Medium | `[e.g. 2]` |
| Low | `[e.g. 1]` |
| Attack chain demonstrated | Yes — guest to full confidential data access |

**Most significant risk:** An unauthenticated/low-privileged attacker can chain **stored XSS** and **missing CSRF protection** to compromise the administrator account, then exploit **SQL injection** and **IDOR** to extract credentials and confidential HR records (salary, SSN, internal notes).

**Overall recommendation:** `[e.g. Do not deploy to production. Address all findings before any real-world use. Priority: input validation, output encoding, parameterized queries, object-level access control, CSRF tokens, and security headers.]`

---

## 2. Scope

### 2.1 In Scope

| Asset | Details |
|-------|---------|
| **Target application** | FakeCompany Internal Portal |
| **Base URL** | `http://[TARGET_VM_IP]/` |
| **Technology stack** | Python Flask, SQLite, nginx reverse proxy |
| **Testing type** | Web application penetration test (Red Team) |

### 2.2 Out of Scope

- `[ ]` Denial of service / load testing
- `[ ]` Social engineering against real personnel
- `[ ]` Physical security
- `[ ]` Active Directory / internal network pivoting *(optional module — document separately if tested)*
- `[ ]` Automated scanning as primary evidence *(scanners may be mentioned for comparison only)*

### 2.3 Rules of Engagement

- Testing performed only in an isolated VM lab owned by the tester
- No testing against production or third-party systems
- All exploitation was manual and documented with reproducible PoCs

---

## 3. Methodology

Testing aligned with **OWASP WSTG** phases:

| Phase | Activities performed |
|-------|---------------------|
| **Information gathering** | Mapped routes, identified roles (guest, employee, admin), reviewed login and session behavior |
| **Configuration & deployment** | Checked missing security headers (`X-Frame-Options`, CSP) |
| **Identity management** | Tested authentication, session handling, password change flow |
| **Authorization** | Tested horizontal access control on `/hr/record/<id>` |
| **Input validation** | Tested feedback form, search parameter for injection |
| **Client-side** | Tested stored XSS, CSRF via XSS, clickjacking |
| **Reporting** | CVSS v3.1 scoring, OWASP Top 10:2025 mapping, remediation |

**Primary tools:**

| Tool | Purpose |
|------|---------|
| Burp Suite Community | Proxy, Repeater, request manipulation |
| Firefox + FoxyProxy | Browser-based testing through Burp |
| `[Optional]` sqlmap | Comparison with manual SQLi only |
| Browser DevTools | XSS execution verification, network inspection |

---

## 4. Test Environment

### 4.1 Architecture Diagram

```
┌─────────────┐      :80       ┌──────────────────────────────────────┐
│ Kali Linux  │ ─────────────► │  Target VM (DMZ)                     │
│ + Burp      │                │  nginx → gunicorn → Flask + SQLite    │
└─────────────┘                └──────────────────────────────────────┘
```

### 4.2 Host Details

| Role | Host | OS | IP |
|------|------|----|----|
| Attacker | `[Kali VM]` | `[e.g. Kali Linux 2024.x]` | `[e.g. 192.168.56.10]` |
| Target | `[Target VM]` | `[e.g. Ubuntu 22.04]` | `[e.g. 192.168.56.20]` |

### 4.3 Accounts Used During Testing

| Username | Role | Purpose in test |
|----------|------|-----------------|
| `guest` | guest | Initial foothold, XSS injection |
| `admin` | admin | Victim session for XSS/CSRF chain |
| `admin` (after takeover) | admin | SQLi, post-exploitation |

---

## 5. Attack Chain Summary

`[Narrative paragraph describing the full kill chain — this is what elevates the report above isolated findings.]`

Starting with a **guest** account, the tester submitted a malicious payload to the public feedback form. When an **administrator** reviewed messages, the stored script executed in their browser and changed the admin password via an unprotected POST endpoint. The tester then authenticated as admin, exploited **SQL injection** in the user search feature to extract database contents, and used **IDOR** to access confidential HR records belonging to other employees.

```
Guest account
      ↓
Stored XSS on /contact
      ↓
Admin opens Feedback Inbox
      ↓
XSS → POST /admin/settings/password (no CSRF token)
      ↓
Attacker logs in as admin
      ↓
SQL Injection on /admin/search
      ↓
Database extraction
      ↓
IDOR on /hr/record/<id>
      ↓
Confidential employee records exposed
```

---

## 6. Findings Summary

| ID | Title | Severity | CVSS | OWASP Top 10:2025 | Type |
|----|-------|----------|------|-------------------|------|
| F-01 | Stored Cross-Site Scripting (XSS) | High | `[7.1]` | A03 Injection | Client-side |
| F-02 | Cross-Site Request Forgery (CSRF) on Password Change | High | `[8.1]` | A01 Broken Access Control | Client-side |
| F-03 | Clickjacking — Missing Frame Protection | Medium | `[4.3]` | A01 Broken Access Control | Client-side |
| F-04 | SQL Injection in Account Lookup | Critical | `[9.8]` | A03 Injection | Server-side |
| F-05 | Insecure Direct Object Reference (IDOR) in HR Records | High | `[6.5]` | A01 Broken Access Control | Server-side |

> Adjust CVSS scores after calculating with the [FIRST CVSS v3.1 Calculator](https://www.first.org/cvss/calculator/3.1).

---

## 7. Detailed Findings

> Duplicate the **Finding Template** below for each vulnerability. Five examples for FakeCompany are pre-filled — customize with your screenshots and Burp exports.

---

### Finding Template (copy per vulnerability)

```
┌─────────────────────────────────────────────────────────────────┐
│ F-XX │ [Vulnerability Title]                                    │
│ Severity: [Critical / High / Medium / Low]                      │
│ CVSS v3.1: [X.X] — [Vector String]                              │
│ OWASP Top 10:2025: [A0X — Category Name]                        │
│ WSTG: [e.g. WSTG-INPV-02 — Testing for Stored XSS]            │
│ Type: [Client-side / Server-side]                               │
└─────────────────────────────────────────────────────────────────┘
```

#### Description

`[What is the vulnerability? 2–4 sentences in plain language.]`

#### Location

- **URL / Endpoint:** `[e.g. POST /contact]`
- **Parameter / Sink:** `[e.g. message form field → rendered with |safe]`
- **Affected component:** `[e.g. templates/contact.html]`

#### How It Was Found

`[Describe your discovery process — manual review, Burp interception, parameter fuzzing, etc. Reference WSTG test case.]`

1. `[Step 1]`
2. `[Step 2]`
3. `[Step 3]`

#### Proof of Concept

**Payload / Request:**

```http
[Paste raw HTTP request from Burp Repeater, or payload string]
```

**Steps to reproduce:**

1. `[...]`
2. `[...]`
3. `[...]`

**Evidence:**

`[Insert screenshot: Figure X — Stored XSS executing in admin browser]`

`[Insert screenshot: Figure X — Burp Repeater showing SQLi response]`

#### Impact

`[What can an attacker achieve? Tie to business impact: account takeover, PII exposure, compliance violation.]`

#### CVSS v3.1 Justification

| Metric | Value | Rationale |
|--------|-------|-----------|
| Attack Vector (AV) | `[Network / Adjacent / Local / Physical]` | `[...]` |
| Attack Complexity (AC) | `[Low / High]` | `[...]` |
| Privileges Required (PR) | `[None / Low / High]` | `[...]` |
| User Interaction (UI) | `[None / Required]` | `[...]` |
| Scope (S) | `[Unchanged / Changed]` | `[...]` |
| Confidentiality (C) | `[None / Low / High]` | `[...]` |
| Integrity (I) | `[None / Low / High]` | `[...]` |
| Availability (A) | `[None / Low / High]` | `[...]` |

**Score:** `[X.X]` · **Vector:** `CVSS:3.1/AV:_/AC:_/PR:_/UI:_/S:_/C:_/I:_/A:_`

#### Remediation

`[Specific, actionable fix — not generic advice.]`

| Priority | Recommendation |
|----------|----------------|
| **Immediate** | `[...]` |
| **Short-term** | `[...]` |
| **Long-term** | `[...]` |

**Secure code example (if applicable):**

```python
# Vulnerable
query = f"... FROM users WHERE username = '{username}'"

# Fixed
cursor.execute(
    "SELECT id, username, role, email FROM users WHERE username = ?",
    (username,),
)
```

#### References

- OWASP: `[URL]`
- WSTG: `[URL]`
- CWE: `[CWE-XXX]`

---

### F-01 — Stored Cross-Site Scripting (XSS)

| Field | Value |
|-------|-------|
| **Severity** | High |
| **CVSS v3.1** | 7.1 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:H/A:N` |
| **OWASP** | A03 — Injection |
| **WSTG** | WSTG-INPV-02 (Stored XSS) |
| **Type** | Client-side |

#### Description

User-supplied feedback on `/contact` is stored and rendered without output encoding (`{{ message|safe }}`). An attacker can inject arbitrary JavaScript that executes in the browser of any user who views the feedback page — including administrators.

#### Location

- **Endpoint:** `POST /contact`
- **Parameter:** `message`
- **Sink:** `templates/contact.html` — Jinja2 `|safe` filter

#### How It Was Found

1. Logged in as `guest` and navigated to `/contact`
2. Submitted `<script>alert(1)</script>` in the message field
3. Observed the script executing on page reload — confirming stored XSS (WSTG-INPV-02)

#### Proof of Concept

```html
<img src=x onerror="fetch('/admin/settings/password',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'new_password=pwned123&confirm_password=pwned123',credentials:'include'})">
```

`[Screenshot: payload in feedback form]`  
`[Screenshot: admin page after viewing /contact]`

#### Impact

Session riding, account takeover when chained with CSRF, defacement, malware delivery to internal users.

#### Remediation

- Remove the `|safe` filter; rely on Jinja2 auto-escaping
- Implement Content-Security-Policy: `script-src 'self'`
- Consider sanitizing rich text with a vetted library if HTML is required

---

### F-02 — Cross-Site Request Forgery (CSRF) on Password Change

| Field | Value |
|-------|-------|
| **Severity** | High |
| **CVSS v3.1** | 8.1 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N` |
| **OWASP** | A01 — Broken Access Control |
| **WSTG** | WSTG-SESS-05 (CSRF) |
| **Type** | Client-side |

#### Description

The administrator password change endpoint (`POST /admin/settings/password`) accepts state-changing requests without a CSRF token, SameSite cookie enforcement, or Referer validation. Combined with stored XSS, an attacker can change the admin password without the victim's knowledge.

#### Location

- **Endpoint:** `POST /admin/settings/password`
- **Parameters:** `new_password`, `confirm_password`

#### How It Was Found

1. Captured the password change request in Burp while logged in as admin
2. Replayed the request without CSRF token — succeeded (WSTG-SESS-05)
3. Chained with F-01 to demonstrate full account takeover without direct admin interaction beyond viewing feedback

#### Proof of Concept

```http
POST /admin/settings/password HTTP/1.1
Host: [TARGET_VM_IP]
Content-Type: application/x-www-form-urlencoded
Cookie: session=[ADMIN_SESSION_COOKIE]

new_password=pwned123&confirm_password=pwned123
```

`[Screenshot: Burp Repeater — 200 OK after password change]`

#### Impact

Full administrator account compromise; gateway to SQL injection and all admin-only functionality.

#### Remediation

- Add CSRF tokens (Flask-WTF or double-submit cookie pattern)
- Set session cookie: `SameSite=Strict; Secure; HttpOnly`
- Require current password before allowing password change

---

### F-03 — Clickjacking (Missing Frame Protection)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **CVSS v3.1** | 4.3 — `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N` |
| **OWASP** | A01 — Broken Access Control |
| **WSTG** | WSTG-CLNT-09 (Clickjacking) |
| **Type** | Client-side |

#### Description

The application does not send `X-Frame-Options` or `Content-Security-Policy: frame-ancestors` headers. Sensitive pages (e.g. password change) can be embedded in a malicious iframe, tricking authenticated users into clicking hidden UI elements.

#### Location

- **All responses** — missing security headers from nginx/Flask
- **PoC file:** `static/poc/clickjacking.html`

#### How It Was Found

1. Reviewed HTTP response headers in Burp — no frame protection (WSTG-CLNT-09)
2. Created HTML page with transparent iframe overlaying decoy content
3. Loaded `/admin/settings/password` in iframe — page rendered inside attacker-controlled frame

#### Proof of Concept

`[Screenshot: clickjacking PoC with invisible iframe over fake "Claim reward" button]`

#### Impact

Trick authenticated users into performing unintended actions (password change, form submission).

#### Remediation

```nginx
add_header X-Frame-Options "DENY" always;
add_header Content-Security-Policy "frame-ancestors 'none'" always;
```

---

### F-04 — SQL Injection in Account Lookup

| Field | Value |
|-------|-------|
| **Severity** | Critical |
| **CVSS v3.1** | 9.8 — `CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H` |
| **OWASP** | A03 — Injection |
| **WSTG** | WSTG-INPV-05 (SQL Injection) |
| **Type** | Server-side |

#### Description

The `username` parameter in `/admin/search` is concatenated directly into a SQL query without sanitization or parameterization. The UI presents a normal account lookup form with no visible SQL — injection must be discovered by testing the input field (WSTG-INPV-05). An attacker with admin access can extract arbitrary data from the database.

#### Location

- **Endpoint:** `GET /admin/search?username=`
- **Parameter:** `username`
- **Vulnerable code pattern:** `f"... FROM users WHERE username = '{username}'"`

#### How It Was Found

1. Logged in as admin after account takeover and opened **Account Lookup**
2. Submitted `'` in the username field — application returned a generic error (syntax break)
3. Submitted `admin' OR '1'='1'--` — all accounts returned in the results table
4. Used UNION-based injection (4 columns) to extract passwords and `hr_records` data

#### Proof of Concept

**Boolean-based:**
```
admin' OR '1'='1'--
```

**UNION — extract credentials** (passwords appear in the Role column):
```
' UNION SELECT id, username, password, email FROM users--
```

**UNION — extract HR records:**
```
' UNION SELECT employee_id, salary, ssn, internal_notes FROM hr_records--
```

```http
GET /admin/search?username=admin'%20OR%20'1'%3D'1'-- HTTP/1.1
Host: [TARGET_VM_IP]
Cookie: session=[SESSION]
```

`[Screenshot: Account Lookup results showing multiple users after OR injection]`  
`[Screenshot: UNION query — anomalous values in Role/Email columns revealing SSN and salary]`

#### Impact

Full database read access — user credentials, salaries, SSNs, internal security notes. The application does not display passwords in normal search results, but SQLi bypasses that UI restriction.

#### Remediation

```python
cursor.execute(
    "SELECT id, username, role, email FROM users WHERE username = ?",
    (username,),
)
```

- Use parameterized queries exclusively (ORM or prepared statements)
- Apply least-privilege DB account (read-only if search only needs SELECT)
- Return generic errors to the client; log SQL errors server-side only

---

### F-05 — Insecure Direct Object Reference (IDOR) in HR Records

| Field | Value |
|-------|-------|
| **Severity** | High |
| **CVSS v3.1** | 6.5 — `CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N` |
| **OWASP** | A01 — Broken Access Control |
| **WSTG** | WSTG-ATHZ-04 (Insecure Direct Object References) |
| **Type** | Server-side |

#### Description

The endpoint `/hr/record/<employee_id>` returns confidential HR data (salary, SSN, internal notes) for any valid employee ID. The application checks that the user is authenticated but does **not** verify that the requester owns or is authorized to view the requested record.

#### Location

- **Endpoint:** `GET /hr/record/<id>`
- **Objects:** Employee IDs 1, 2, 3

#### How It Was Found

1. Logged in as `guest` (low-privilege account)
2. Manually incremented `employee_id` in the URL: `/hr/record/1`, `/hr/record/2`, etc. (WSTG-ATHZ-04)
3. Retrieved confidential PII for employees other than the authenticated user

#### Proof of Concept

```http
GET /hr/record/2 HTTP/1.1
Host: [TARGET_VM_IP]
Cookie: session=[GUEST_SESSION]
```

`[Screenshot: guest session viewing Alex Ivanov's salary and SSN]`

#### Impact

Horizontal privilege escalation — any authenticated user can access sensitive HR data for all employees. GDPR / compliance violation.

#### Remediation

```python
# Verify ownership before returning record
user = current_user()
if user.role != "admin" and user.employee_id != employee_id:
    abort(403)
```

- Enforce object-level authorization on every data access
- Use indirect references (UUIDs) where possible
- Log and alert on cross-user access attempts

---

## 8. Remediation Roadmap

| Priority | Finding | Effort | Owner |
|----------|---------|--------|-------|
| P0 — Immediate | F-04 SQL Injection | Low | Development |
| P0 — Immediate | F-01 Stored XSS | Low | Development |
| P1 — High | F-02 CSRF | Medium | Development |
| P1 — High | F-05 IDOR | Medium | Development |
| P2 — Medium | F-03 Clickjacking | Low | Infrastructure / DevOps |

---

## 9. Conclusion

`[Summarize what was tested, the overall security posture, and what you learned.]`

The FakeCompany portal demonstrates how individually "medium" vulnerabilities combine into a **critical business risk**. Client-side flaws (XSS, CSRF) enabled server-side exploitation (SQLi, IDOR) without advanced tooling. Manual testing following WSTG provided full coverage and reproducible evidence suitable for defensive remediation.

**Testing completed:** `[Date]`  
**Retest recommended after fixes:** `[Yes / No]`

---

## 10. Appendices

### Appendix A — Full Burp Request/Response Log

`[Attach or reference exported Burp project / request files]`

### Appendix B — Screenshot Index

| Figure | Description | Finding |
|--------|-------------|---------|
| Fig. 1 | Lab network topology | Section 4 |
| Fig. 2 | Stored XSS payload submission | F-01 |
| Fig. 3 | Admin password changed via XSS | F-02 |
| Fig. 4 | SQLi — all users extracted | F-04 |
| Fig. 5 | IDOR — guest views HR record #2 | F-05 |

### Appendix C — CVSS Calculator Screenshots

`[Optional: screenshot from first.org CVSS calculator for each finding]`

### Appendix D — Tools & Versions

| Tool | Version |
|------|---------|
| Burp Suite | `[e.g. 2024.x]` |
| Firefox | `[version]` |
| Kali Linux | `[version]` |
| Target OS | `[version]` |

---

*End of report template*
