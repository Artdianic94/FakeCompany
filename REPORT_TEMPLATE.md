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

**Most significant risk:** An attacker with a guest account can chain **stored XSS** and **CSRF** to hijack the administrator session, then use **SQL injection** to extract HR PII access codes from the database and unlock confidential personnel data (salary, SSN, internal notes) that the application intentionally gates behind a secondary verification step.

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
| `admin` (after takeover) | admin | HR file review, SQLi, PII unlock |

---

## 5. Attack Chain Summary

`[Narrative paragraph describing the full kill chain — this is what elevates the report above isolated findings.]`

Starting with a **guest** account, the tester submitted a malicious payload to the public feedback form. When an **administrator** reviewed messages, the stored script changed the admin password via an unprotected POST endpoint. After authenticating as admin, the tester opened an employee HR file from the admin dashboard — obtaining only contact details while PII remained locked behind an HR access code. **SQL injection** in Account Lookup extracted `pii_access_code` values from the `hr_records` table. The tester entered the stolen code on the HR file page and unlocked salary, SSN, and internal notes for the target employee.

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
Admin → Open HR file → contact info only, PII locked
      ↓
SQL Injection → extract pii_access_code from hr_records
      ↓
Enter stolen code → salary, SSN, internal notes revealed
```

---

## 6. Findings Summary

| ID | Title | Severity | CVSS | OWASP Top 10:2025 | Type |
|----|-------|----------|------|-------------------|------|
| F-01 | Stored Cross-Site Scripting (XSS) | High | `[7.1]` | A03 Injection | Client-side |
| F-02 | Cross-Site Request Forgery (CSRF) on Password Change | High | `[8.1]` | A01 Broken Access Control | Client-side |
| F-03 | Clickjacking — Missing Frame Protection | Medium | `[4.3]` | A01 Broken Access Control | Client-side |
| F-04 | SQL Injection in Account Lookup | Critical | `[9.8]` | A03 Injection | Server-side |
| F-05 | PII Exposure via Leaked HR Access Codes | High | `[7.5]` | A01 Broken Access Control | Server-side |

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

The `username` parameter in `/admin/search` is concatenated directly into a SQL query without sanitization or parameterization. An attacker with admin access can use UNION-based injection to read arbitrary tables — including `hr_records`, which stores `pii_access_code` values that gate access to confidential HR data.

#### Location

- **Endpoint:** `GET /admin/search?username=`
- **Parameter:** `username`
- **Vulnerable code pattern:** `f"... FROM users WHERE username = '{username}'"`

#### How It Was Found

1. Logged in as admin after account takeover; opened an HR file — PII section locked behind access code
2. Opened **Account Lookup**; submitted `'` — generic error returned
3. Submitted `admin' OR '1'='1'--` — multiple rows returned
4. Used UNION injection to extract `pii_access_code` from `hr_records` (WSTG-INPV-05)

#### Proof of Concept

**Boolean-based:**
```
admin' OR '1'='1'--
```

**UNION — extract HR PII access codes:**
```
' UNION SELECT employee_id, pii_access_code, phone, office_extension FROM hr_records--
```

```http
GET /admin/search?username='+%UNION+SELECT+employee_id,+pii_access_code,+phone,+office_extension+FROM+hr_records-- HTTP/1.1
Host: [TARGET_VM_IP]
Cookie: session=[ADMIN_SESSION]
```

`[Screenshot: UNION results — PII-A2-9B2C visible in Username column for employee_id=2]`

#### Impact

Extracts HR PII access codes from the database, bypassing the application's secondary verification control. Enables full personnel data exposure when combined with F-05.

#### Remediation

```python
cursor.execute(
    "SELECT id, username, role, email FROM users WHERE username = ?",
    (username,),
)
```

- Use parameterized queries exclusively
- Store access codes outside the application database (secrets manager)
- Apply least-privilege DB permissions — search query should not reach `hr_records`

---

### F-05 — PII Exposure via Leaked HR Access Codes

| Field | Value |
|-------|-------|
| **Severity** | High |
| **CVSS v3.1** | 7.5 — `CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:N/A:N` |
| **OWASP** | A01 — Broken Access Control |
| **WSTG** | WSTG-ATHN-05 (Testing for Weak Security Question/Answer) / defense-in-depth failure |
| **Type** | Server-side |

#### Description

Employee HR files at `/admin/hr/<employee_id>` show contact information to administrators but gate PII (salary, SSN, internal notes) behind an HR access code. The codes are stored in plaintext in `hr_records.pii_access_code`. Combined with SQL injection (F-04), an attacker can obtain the code and unlock the confidential section — rendering the access control meaningless.

#### Location

- **Endpoint:** `GET/POST /admin/hr/<employee_id>`
- **Parameter:** `access_code` (POST form)
- **Secret storage:** `hr_records.pii_access_code` column

#### How It Was Found

1. As admin, opened **Employee HR files → Alex Ivanov** — saw phone/extension only; PII form displayed
2. SQL injection (F-04) returned `PII-A2-9B2C` for employee_id 2
3. Submitted stolen code on the HR file page — PII section unlocked with salary and SSN

#### Proof of Concept

```http
POST /admin/hr/2 HTTP/1.1
Host: [TARGET_VM_IP]
Cookie: session=[ADMIN_SESSION]
Content-Type: application/x-www-form-urlencoded

access_code=PII-A2-9B2C
```

`[Screenshot: HR file before unlock — PII form visible]`  
`[Screenshot: HR file after unlock — salary $112,000 and SSN displayed]`

#### Impact

Full PII exposure for any employee record once the static access code is obtained via SQLi. GDPR/compliance violation; demonstrates failure of defense-in-depth when secrets live in the same database as application data.

#### Remediation

- Never store access codes in the same database reachable by application queries
- Use per-session OTP, hardware tokens, or HR-only identity provider for PII access
- Hash codes if stored locally; implement rate limiting and lockout on failed attempts
- Log and alert on PII section unlock events

---

## 8. Remediation Roadmap

| Priority | Finding | Effort | Owner |
|----------|---------|--------|-------|
| P0 — Immediate | F-04 SQL Injection | Low | Development |
| P0 — Immediate | F-01 Stored XSS | Low | Development |
| P1 — High | F-02 CSRF | Medium | Development |
| P1 — High | F-05 PII via leaked codes | Medium | Development |
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
| Fig. 4 | SQLi — UNION extract of PII access codes | F-04 |
| Fig. 5 | HR file unlocked after entering stolen code | F-05 |

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
