# Digital Scam Evidence & Connection Mapper

A beginner-friendly Flask + MySQL learning project. People can submit a short description of a suspected scam and optional evidence (phone, email, URL, payment ID, or other). The database stores evidence once and links it to many reports. The home page shows possible repeated signals without publishing the evidence values.

> This is a class project, not an official reporting service or a verification system. Reports are unverified, and a shared detail is only a lead for human review. Do not submit passwords, complete card numbers, government ID numbers, private chats, or information you are not comfortable sharing with the site operator. Before running a public community site, add moderation, abuse controls, a privacy notice, and a secure deletion process.

## Project files

- `app.py` — Flask routes, validation, and parameterized MySQL queries.
- `create_reviewer.py` — securely create a reviewer account with a hashed password.
- `schema.sql` — normalized schema and a sample aggregate query.
- `seed.sql` — fictional sample records. Run only after `schema.sql`.
- `templates/` — HTML pages.
- `static/` — CSS and browser-side JavaScript.
- `.env.example` — settings template. Copy it to `.env` and fill in local values. Never upload `.env`.

## 1. Install the tools

Install Python 3.10 or newer, MySQL Server 8, and Visual Studio Code. In VS Code, open the `scam-mapper` folder. Open the integrated terminal from **Terminal → New Terminal**.

## 2. Create the database

Open MySQL Workbench, connect to your local MySQL server, open `schema.sql`, and click the lightning-bolt execute button. Then create an application user with limited access (choose your own password):

```sql
CREATE USER 'scam_app'@'localhost' IDENTIFIED BY 'choose-a-long-password';
GRANT SELECT, INSERT, UPDATE ON scam_mapper.* TO 'scam_app'@'localhost';
```

If your Flask app connects over TCP and MySQL does not accept `localhost`, create the user for `127.0.0.1` instead. Optional: run `seed.sql` in Workbench to insert fictional examples.

## 3. Run the website locally

In the VS Code terminal, run these commands from the project folder. On Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in VS Code and set `FLASK_SECRET_KEY` to a long random value and `DB_PASSWORD` to the MySQL password. Keep the database settings aligned with the user you created. Then start Flask:

```powershell
python app.py
```

Open `http://127.0.0.1:5000` in your browser. Stop the server with Ctrl+C in the terminal.

## Reviewer sign-in and report review

The private reviewer area allows an authorized reviewer to inspect submissions and mark them **reviewed** or **closed**. Every status change is recorded in `audit_log`. There is no public reviewer registration.

1. Run the updated `schema.sql` in MySQL Workbench to add the `reviewers` table to an existing database. (The `CREATE TABLE IF NOT EXISTS` statements are safe to run again.)
2. Make sure the MySQL application user has `SELECT` and `INSERT` permission on `reviewers` in addition to its existing permissions. For example, run this in Workbench as a database administrator:

   ```sql
   GRANT SELECT, INSERT ON scam_mapper.reviewers TO 'scam_app'@'localhost';
   ```

3. Activate the virtual environment and install the updated requirements: `pip install -r requirements.txt`.
4. Run `python create_reviewer.py` in the terminal. Enter a username and a password of at least 12 characters when prompted. The password is saved only as a one-way password hash; it is not written into the project files.
5. Start the app and click **Reviewer sign in** in the navigation bar. The reviewer can inspect the queue and select **Mark reviewed** or **Close report**.

Use a private reviewer account only for trusted people. Set a unique, long `FLASK_SECRET_KEY` in `.env`. On an HTTPS deployment, set `COOKIE_SECURE=1`; keep it `0` for local `http://127.0.0.1` development.

If PowerShell blocks virtual-environment activation, use Command Prompt and run `.venv\Scripts\activate.bat`, then continue with `pip install -r requirements.txt`.

## 4. Upload the project to GitHub

Create a new **empty** repository on GitHub. In the VS Code terminal, from this project folder:

```powershell
git init
git add .
git commit -m "Build scam evidence mapper"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

Replace the remote address with your repository's address. `.gitignore` excludes `.env` and your local virtual environment. Before pushing, check that no passwords or real personal data appear in files or commits.

## 5. Put it online (Render + a hosted MySQL database)

The app needs both a Python web host and a reachable MySQL 8 database. Create a hosted MySQL database with a provider that allows connections from your web host; note its host, port, database name, username, and password. Follow that provider's instructions to run `schema.sql` against the new database. Do not use sample real-person reports.

1. Push the project to GitHub as above.
2. In Render, create **New → Web Service** and connect the repository.
3. Set the root directory to `scam-mapper` if you uploaded the parent folder; otherwise leave it blank.
4. Set the build command to `pip install -r requirements.txt` and start command to `gunicorn app:app`.
5. Add environment variables in the Render service settings: `FLASK_SECRET_KEY` (a newly generated long random secret), `FLASK_DEBUG=0`, and `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` from the database provider.
6. Deploy, then open the `onrender.com` address shown for the service. Submit a fictional test report and confirm it appears as expected.

Keep database credentials private, restrict database network access when the provider supports it, and use HTTPS. A public demo can receive spam or harmful content. Add moderation and operational safeguards before inviting broad public use. Hosting plans, database availability, and pricing change; check the host's current terms before choosing a plan.

## Database concepts demonstrated

- **Normalization:** reports, evidence, and their many-to-many link live in separate tables.
- **Joins:** `report_evidence` connects a report to its evidence.
- **Duplicate detection:** unique evidence values are reused across reports.
- **Aggregate query:** `schema.sql` shows how to count shared evidence by distinct reports.
- **Audit log:** each submission records a simple timestamped event.
- **Security basics:** SQL uses placeholders; input has length/format checks; `.env` is excluded from Git.

The current learning version intentionally has no account system. It has no user authentication, admin moderation screen, or automated proof/verification. Public text is user supplied; database submissions should be reviewed before being treated as factual.
