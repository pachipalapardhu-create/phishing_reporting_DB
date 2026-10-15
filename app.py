import os
import re
from datetime import date
from urllib.parse import urlparse

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from mysql.connector import IntegrityError
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from functools import wraps

load_dotenv()
app = Flask(__name__)
app.config.update(SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-only-change-me"), MAX_CONTENT_LENGTH=32 * 1024)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1")
CSRFProtect(app)

KINDS = {"phone": "Phone number", "email": "Email address", "url": "Website URL", "payment_id": "Payment ID", "other": "Other"}

def db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "scam_app"), password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "scam_mapper"), charset="utf8mb4",
    )

def normalize(kind, value):
    value = value.strip()
    if not value or len(value) > 512 or any(ord(c) < 32 for c in value):
        raise ValueError("Evidence must be between 1 and 512 characters.")
    if kind == "email":
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value): raise ValueError("Enter a valid email address.")
        return value.lower()
    if kind == "url":
        parsed = urlparse(value if "://" in value else "https://" + value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or "." not in parsed.hostname: raise ValueError("Enter a valid website URL.")
        return parsed.geturl().lower()
    if kind == "phone":
        if not re.fullmatch(r"\+?[0-9 ()-]{7,30}", value): raise ValueError("Enter a valid phone number.")
        return re.sub(r"\D", "", value)
    return value.casefold()

def mask(value):
    if "@" in value:
        name, domain = value.split("@", 1); return (name[:1] + "•••@" + domain) if name else "•••@" + domain
    parsed = urlparse(value)
    if parsed.hostname:
        return parsed.hostname + ("/•••" if parsed.path and parsed.path != "/" else "")
    return "••••" + value[-3:] if len(value) > 3 else "•••"

def reviewer_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("reviewer_id"):
            return redirect(url_for("review_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    conn = db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT r.id,r.title,r.description,r.created_at, COUNT(re.evidence_id) evidence_count FROM reports r LEFT JOIN report_evidence re ON re.report_id=r.id WHERE r.status <> 'closed' GROUP BY r.id ORDER BY r.created_at DESC LIMIT 50")
    reports = cur.fetchall()
    cur.execute("SELECT COUNT(*) n FROM reports WHERE status <> 'closed'"); report_count = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) n FROM evidence"); evidence_count = cur.fetchone()["n"]
    cur.execute("SELECT e.kind, COUNT(DISTINCT re.report_id) report_count FROM evidence e JOIN report_evidence re ON re.evidence_id=e.id GROUP BY e.id HAVING report_count >= 2 ORDER BY report_count DESC LIMIT 8")
    connections = cur.fetchall(); cur.close(); conn.close()
    return render_template("index.html", reports=reports, report_count=report_count, evidence_count=evidence_count, connections=connections)

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "GET": return render_template("report.html", kinds=KINDS)
    title = request.form.get("title", "").strip(); description = request.form.get("description", "").strip()
    if not title or len(title) > 120 or len(description) < 15 or len(description) > 2000:
        flash("Add a short title and a description between 15 and 2,000 characters.", "error"); return render_template("report.html", kinds=KINDS), 400
    kinds = request.form.getlist("evidence_kind[]"); values = request.form.getlist("evidence_value[]")
    if len(kinds) != len(values) or len(kinds) > 12:
        flash("Please add up to 12 complete evidence items.", "error"); return render_template("report.html", kinds=KINDS), 400
    prepared = []
    try:
        for kind, value in zip(kinds, values):
            if not value.strip(): continue
            if kind not in KINDS: raise ValueError("Choose a listed evidence type.")
            prepared.append((kind, normalize(kind, value)))
    except ValueError as exc:
        flash(str(exc), "error"); return render_template("report.html", kinds=KINDS), 400
    incident = request.form.get("incident_date") or None
    if incident:
        try:
            if date.fromisoformat(incident) > date.today(): raise ValueError()
        except ValueError:
            flash("Choose a valid date that is not in the future.", "error"); return render_template("report.html", kinds=KINDS), 400
    conn = db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO reports(title,description,incident_date) VALUES (%s,%s,%s)", (title, description, incident))
        report_id = cur.lastrowid
        for kind, value in prepared:
            cur.execute("INSERT INTO evidence(kind,value_normalized,value_display) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id)", (kind, value, value))
            evidence_id = cur.lastrowid
            cur.execute("INSERT IGNORE INTO report_evidence(report_id,evidence_id) VALUES (%s,%s)", (report_id, evidence_id))
        cur.execute("INSERT INTO audit_log(report_id,action,details) VALUES (%s,%s,%s)", (report_id, "report_submitted", "Public report submitted"))
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()
    flash("Report submitted. Shared evidence matches are only possible connections and need human review.", "success")
    return redirect(url_for("index"))

@app.route("/review/login", methods=["GET", "POST"])
def review_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        conn = db(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,username,password_hash FROM reviewers WHERE username=%s", (username,))
        reviewer = cur.fetchone(); cur.close(); conn.close()
        if reviewer and check_password_hash(reviewer["password_hash"], password):
            session.clear(); session["reviewer_id"] = reviewer["id"]; session["reviewer_name"] = reviewer["username"]
            return redirect(url_for("review_queue"))
        flash("Username or password was not recognized.", "error")
    return render_template("review_login.html")

@app.post("/review/logout")
@reviewer_required
def review_logout():
    session.clear(); flash("You have signed out.", "success")
    return redirect(url_for("index"))

@app.get("/review")
@reviewer_required
def review_queue():
    conn = db()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            r.id,
            r.title,
            r.description,
            r.incident_date,
            r.status,
            r.created_at,
            e.kind AS evidence_kind,
            e.value_display AS evidence_value
        FROM reports AS r
        LEFT JOIN report_evidence AS re ON re.report_id = r.id
        LEFT JOIN evidence AS e ON e.id = re.evidence_id
        ORDER BY
            FIELD(r.status, 'new', 'reviewed', 'closed'),
            r.created_at DESC,
            e.kind
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    reports_by_id = {}

    for row in rows:
        report = reports_by_id.setdefault(row["id"], {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "incident_date": row["incident_date"],
            "status": row["status"],
            "created_at": row["created_at"],
            "evidence": [],
        })

        if row["evidence_kind"]:
            report["evidence"].append({
                "kind": row["evidence_kind"],
                "value": row["evidence_value"],
            })

    return render_template(
        "review_queue.html",
        reports=list(reports_by_id.values()),
        kinds=KINDS,
    )


@app.post("/review/<int:report_id>/status")
@reviewer_required
def update_review_status(report_id):
    status = request.form.get("status")

    if status not in ("reviewed", "closed"):
        flash("Choose a valid review outcome.", "error")
        return redirect(url_for("review_queue"))

    conn = db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE reports SET status=%s WHERE id=%s",
        (status, report_id),
    )

    if cur.rowcount:
        cur.execute(
            "INSERT INTO audit_log(report_id, action, details) VALUES (%s, %s, %s)",
            (
                report_id,
                "status_changed",
                f"Status set to {status} by reviewer",
            ),
        )
        conn.commit()
        flash(f"Report #{report_id} marked {status}.", "success")
    else:
        conn.rollback()
        flash("Report not found.", "error")

    cur.close()
    conn.close()
    return redirect(url_for("review_queue"))
@app.errorhandler(413)
def too_large(_): return "Submission too large.", 413

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
