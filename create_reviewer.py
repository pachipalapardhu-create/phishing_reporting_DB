"""Create a reviewer account interactively; the password is never stored as plain text."""
import getpass
import os
import re

import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()
username = input("Reviewer username (3-80 letters, numbers, _ or -): ").strip()
if not re.fullmatch(r"[A-Za-z0-9_-]{3,80}", username):
    raise SystemExit("Choose a username with 3-80 letters, numbers, underscores, or hyphens.")
password = getpass.getpass("Reviewer password (at least 12 characters): ")
if len(password) < 12:
    raise SystemExit("Password must contain at least 12 characters.")
confirm = getpass.getpass("Confirm password: ")
if password != confirm:
    raise SystemExit("Passwords did not match.")
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "scam_app"), password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "scam_mapper"), charset="utf8mb4",
)
try:
    cur = conn.cursor()
    cur.execute("INSERT INTO reviewers(username,password_hash) VALUES (%s,%s)", (username, generate_password_hash(password)))
    conn.commit()
    print(f"Reviewer account '{username}' created.")
except mysql.connector.IntegrityError:
    conn.rollback()
    raise SystemExit("That reviewer username already exists.")
finally:
    conn.close()
