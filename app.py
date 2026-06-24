import os
import re
import sqlite3
import subprocess
from datetime import datetime

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fakecompany-secret-key-change-in-prod")

DATABASE = os.environ.get("DATABASE_PATH", "fakecompany.db")
UNSAFE_COMMANDS = os.environ.get("FAKECOMPANY_UNSAFE_COMMANDS") == "1"
_INJECTION_PATTERN = re.compile(r"[;&|`$()<>]|&&|\|\|")
_HOST_PATTERN = re.compile(r"^[a-zA-Z0-9.\-]+$")

PUBLIC_EMPLOYEES = [
    {
        "id": 1,
        "name": "Diana Petrova",
        "role": "Security Analyst",
        "email": "diana@fakecompany.local",
        "department": "Information Security",
    },
    {
        "id": 2,
        "name": "Alex Ivanov",
        "role": "System Administrator",
        "email": "alex@fakecompany.local",
        "department": "IT Operations",
    },
    {
        "id": 3,
        "name": "Maria Sokolova",
        "role": "HR Manager",
        "email": "maria@fakecompany.local",
        "department": "Human Resources",
    },
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_column(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cursor.fetchall()}
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT,
            employee_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS hr_records (
            employee_id INTEGER PRIMARY KEY,
            phone TEXT,
            office_extension TEXT,
            pii_access_code TEXT,
            salary TEXT,
            ssn TEXT,
            internal_notes TEXT,
            personal_address TEXT
        );
        """
    )

    _ensure_column(cursor, "users", "email", "TEXT")
    _ensure_column(cursor, "users", "employee_id", "INTEGER")
    _ensure_column(cursor, "hr_records", "phone", "TEXT")
    _ensure_column(cursor, "hr_records", "office_extension", "TEXT")
    _ensure_column(cursor, "hr_records", "pii_access_code", "TEXT")
    db.commit()

    seed_users = [
        ("guest", "guest123", "guest", "guest@fakecompany.local", None),
        ("admin", "admin123", "admin", "admin@fakecompany.local", None),
        ("diana", "diana2024!", "employee", "diana@fakecompany.local", 1),
        ("alex", "sysadmin99", "employee", "alex@fakecompany.local", 2),
        ("maria", "hr_secure1", "employee", "maria@fakecompany.local", 3),
    ]
    for username, password, role, email, employee_id in seed_users:
        existing = cursor.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE users
                SET password = ?, role = ?, email = ?, employee_id = ?
                WHERE username = ?
                """,
                (password, role, email, employee_id, username),
            )
        else:
            cursor.execute(
                """
                INSERT INTO users (username, password, role, email, employee_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, password, role, email, employee_id),
            )

    seed_hr = [
        (1, "+1-555-0142", "ext. 401", "PII-D1-7F3A", "$94,500", "482-91-7734", "Completed SOC2 audit Q3. VPN access: tier-2.", "14 Oak Street, Suite 4B"),
        (2, "+1-555-0187", "ext. 512", "PII-A2-9B2C", "$112,000", "591-22-8841", "Domain admin credentials in KeePass vault srv-01.", "88 River Road, Apt 12"),
        (3, "+1-555-0199", "ext. 305", "PII-M3-4E8D", "$87,200", "403-55-9920", "Pending background check for contractor batch #7.", "3 Maple Lane"),
    ]
    for record in seed_hr:
        cursor.execute(
            """
            INSERT OR IGNORE INTO hr_records
            (employee_id, phone, office_extension, pii_access_code, salary, ssn, internal_notes, personal_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            record,
        )

    for employee_id, phone, ext, code, salary, ssn, notes, address in seed_hr:
        cursor.execute(
            """
            UPDATE hr_records
            SET phone = ?, office_extension = ?, pii_access_code = ?,
                salary = ?, ssn = ?, internal_notes = ?, personal_address = ?
            WHERE employee_id = ?
            """,
            (phone, ext, code, salary, ssn, notes, address, employee_id),
        )

    db.commit()

    employee_map = {"diana": 1, "alex": 2, "maria": 3}
    for username, employee_id in employee_map.items():
        cursor.execute(
            "UPDATE users SET employee_id = ? WHERE username = ?",
            (employee_id, username),
        )

    db.commit()
    db.close()


def current_user():
    username = session.get("user")
    if not username:
        return None
    db = get_db()
    return db.execute(
        "SELECT id, username, role, email, employee_id FROM users WHERE username = ?",
        (username,),
    ).fetchone()


def login_required(view):
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


def admin_required(view):
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator privileges required.", "error")
            return redirect(url_for("home"))
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


@app.context_processor
def inject_globals():
    return {"current_user": current_user()}


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_db().execute(
            "SELECT username, password, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user and user["password"] == password:
            session["user"] = user["username"]
            session["role"] = user["role"]
            next_url = request.args.get("next") or url_for("home")
            return redirect(next_url)

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/employees")
@login_required
def employee_list():
    return render_template("employees.html", employees=PUBLIC_EMPLOYEES)


@app.route("/profile/<int:employee_id>")
def profile(employee_id):
    employee = next((e for e in PUBLIC_EMPLOYEES if e["id"] == employee_id), None)
    return render_template("profile.html", employee=employee)


@app.route("/admin/hr/<int:employee_id>", methods=["GET", "POST"])
@admin_required
def admin_hr_record(employee_id):
    record = get_db().execute(
        """
        SELECT employee_id, phone, office_extension, pii_access_code,
               salary, ssn, internal_notes, personal_address
        FROM hr_records WHERE employee_id = ?
        """,
        (employee_id,),
    ).fetchone()
    employee = next((e for e in PUBLIC_EMPLOYEES if e["id"] == employee_id), None)

    unlock_key = f"pii_unlocked_{employee_id}"
    pii_unlocked = session.get(unlock_key, False)

    if request.method == "POST" and record:
        submitted = request.form.get("access_code", "").strip()
        if submitted == record["pii_access_code"]:
            session[unlock_key] = True
            pii_unlocked = True
            flash("PII section unlocked.", "success")
        else:
            flash("Invalid HR access code.", "error")

    return render_template(
        "admin_hr_record.html",
        employee=employee,
        record=record,
        pii_unlocked=pii_unlocked,
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        author = session.get("user", "Anonymous")
        if message:
            get_db().execute(
                "INSERT INTO contact_messages (author, message, created_at) VALUES (?, ?, ?)",
                (author, message, datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
            )
            get_db().commit()
            flash("Thank you — your message has been submitted.", "success")
            return redirect(url_for("contact"))

    messages = get_db().execute(
        "SELECT author, message, created_at FROM contact_messages ORDER BY id DESC"
    ).fetchall()

    return render_template("contact.html", messages=messages)


@app.route("/admin")
@admin_required
def admin():
    unread = get_db().execute("SELECT COUNT(*) AS count FROM contact_messages").fetchone()["count"]
    return render_template("admin.html", unread_count=unread, employees=PUBLIC_EMPLOYEES)


@app.route("/admin/search", methods=["GET", "POST"])
@admin_required
def admin_search():
    results = None
    error = None
    username = request.values.get("username", "").strip()

    if username:
        query = (
            "SELECT id, username, role, email "
            f"FROM users WHERE username = '{username}'"
        )
        try:
            cursor = get_db().cursor()
            cursor.execute(query)
            results = cursor.fetchall()
        except sqlite3.Error:
            error = "Unable to complete search. Please check your input and try again."
            results = []

    return render_template(
        "admin_search.html",
        results=results,
        username=username,
        error=error,
        searched=bool(username),
    )


@app.route("/admin/settings/password", methods=["GET", "POST"])
@admin_required
def admin_change_password():
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password or new_password != confirm_password:
            flash("Passwords do not match.", "error")
        else:
            get_db().execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (new_password, session["user"]),
            )
            get_db().commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("admin"))

    return render_template("admin_password.html")


def _simulate_command_injection_output(host):
    """Lab-safe fake output — teaches the vector without executing attacker input."""
    lower = host.lower()
    if "passwd" in lower:
        body = (
            "root:x:0:0:root:/root:/bin/bash\n"
            "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
            "nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin"
        )
    elif "whoami" in lower:
        body = "www-data"
    elif "id" in lower:
        body = "uid=33(www-data) gid=33(www-data) groups=33(www-data)"
    else:
        body = "lab-cmd-simulation-ok"

    return (
        f"$ ping -c 3 {host}\n"
        f"PING 127.0.0.1 (127.0.0.1): 56 data bytes\n"
        f"--- 127.0.0.1 ping statistics ---\n"
        f"3 packets transmitted, 3 received, 0% packet loss\n\n"
        f"{body}\n\n"
        "[FakeCompany lab safe mode — command output simulated; "
        "no OS command was executed on your machine]"
    )


def _run_diagnostics(host):
    """
    Intentionally vulnerable design for the pentest lab:
    user input is concatenated into a shell command.

    By default (safe mode) injection payloads return simulated output only.
    Set FAKECOMPANY_UNSAFE_COMMANDS=1 on an isolated VM for real execution.
    """
    if _INJECTION_PATTERN.search(host):
        if UNSAFE_COMMANDS:
            return subprocess.check_output(
                f"ping -c 3 {host}",
                shell=True,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            ), False
        return _simulate_command_injection_output(host), True

    if not _HOST_PATTERN.fullmatch(host):
        return "Invalid host format. Use letters, digits, dots, or hyphens only.", False

    result = subprocess.run(
        ["ping", "-c", "3", host],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout or result.stderr or "Ping completed with no output.", False


@app.route("/admin/diagnostics", methods=["GET", "POST"])
@admin_required
def admin_diagnostics():
    output = None
    host = ""
    simulated = False

    if request.method == "POST":
        host = request.form.get("host", "").strip()
        if host:
            try:
                output, simulated = _run_diagnostics(host)
            except subprocess.CalledProcessError as exc:
                output = exc.output or str(exc)
            except subprocess.TimeoutExpired:
                output = "Diagnostic command timed out."
            except OSError as exc:
                output = str(exc)

    return render_template(
        "admin_diagnostics.html",
        output=output,
        host=host,
        simulated=simulated,
        unsafe_mode=UNSAFE_COMMANDS,
    )


@app.route("/about")
def about():
    return render_template("about.html")


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG", "1") == "1")
