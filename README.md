# Gamers Nation

Video game tracker app built with Flask.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:
	pip install -r requirements.txt
3. Start the app:
	python server.py
4. Open in browser:
	http://127.0.0.1:5000

### One-command dev start (PostgreSQL + Flask)

Use this in PowerShell from the project root:

1. Start everything:
	.\scripts\start_dev.ps1
2. First run (or after dependency changes):
	.\scripts\start_dev.ps1 -InstallDeps

This command starts Docker PostgreSQL, configures DB environment variables for the current session, and launches Flask.

## Database

This project supports both SQLite and PostgreSQL using the same model/query code.

- Default backend: SQLite
- SQLite file: data/videogames_schema.db
- Tables are auto-created on first use.

### Use PostgreSQL

Quick setup (recommended on Windows with Docker Desktop):

1. Run:
	. .\scripts\setup_postgres.ps1
2. Start app in the same terminal session:
	c:/Users/jerem/Gamers_Nation/.venv/Scripts/python.exe server.py
This quick setup uses host port 15432 to avoid conflicts with any existing local PostgreSQL service.

Manual setup:

1. Install and run PostgreSQL locally (or use a hosted Postgres service).
2. Set environment variables:

	Windows PowerShell example:
	$env:DB_BACKEND="postgres"
	$env:PGHOST="localhost"
	$env:PGPORT="15432"
	$env:PGUSER="postgres"
	$env:PGPASSWORD="your_password"
	$env:PGDATABASE="videogames_schema"

	Optional: you can use one connection string instead:
	$env:DATABASE_URL="postgresql://postgres:your_password@localhost:15432/videogames_schema"

3. Start the app:
	python server.py

If DB_BACKEND is not set to postgres, the app will use SQLite.
If DATABASE_URL is set, it takes precedence over PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE.

### Admin/Superuser

To give yourself admin permissions (edit/delete any game):

1. Ensure Postgres env vars are set in this terminal (or run .\scripts\setup_postgres.ps1).
2. Create or promote your account to admin:
	c:/Users/jerem/Gamers_Nation/.venv/Scripts/python.exe scripts/create_or_promote_admin.py --email your_email@example.com --first-name YourFirstName --last-name YourLastName --password YourStrongPassword

If the email already exists, the script promotes that account to admin.
If the email does not exist, the script creates a new admin account.
