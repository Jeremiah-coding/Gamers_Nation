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

This project supports PostgreSQL and an explicit SQLite mode using the same model/query code.

- Default backend for `server.py`: PostgreSQL in the Docker container on port 15432.
- SQLite file: data/videogames_schema.db
- Tables are auto-created on first use. Server startup checks the selected database and stops with a clear error if it is unavailable; it never silently switches databases.
- To opt into SQLite for isolated local testing, set `$env:LOCAL_DB_BACKEND="sqlite"` before running `python server.py`.

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

If DATABASE_URL is set, it takes precedence over PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE.

## Long-term deployment on Render

The repository includes a paid Render Blueprint in `render.yaml`. It creates a Python web service and a persistent PostgreSQL 16 database in the Ohio region. The service uses Gunicorn, HTTPS, secure session cookies, and Render-managed database credentials. Free database plans are intentionally not used because they expire.

1. Push the deployment files to the GitHub `main` branch.
2. In Render, create a new Blueprint and connect `Jeremiah-coding/Gamers_Nation` on `main`.
3. Review the paid web and database plans and monthly estimate before applying the Blueprint. Render will generate `SECRET_KEY`; enter a new private `TEMPEST_ADMIN_PASSCODE` when prompted. Do not reuse the old local passcode, which has appeared in Git history.
4. Before inviting visitors, copy the existing local PostgreSQL data to the newly created, empty Render database. Run `scripts/migrate_to_render.ps1` from PowerShell with Docker Desktop running, then paste the Render **External Database URL** into its secure prompt. The script aborts rather than overwriting a target that already has a `users` table. Keep the local database as a backup.
5. After migration, restrict the Render database IP allowlist to internal Render connections. The web service uses the private database URL; only reopen external access when you need to do another maintenance migration.
6. Open the Render service URL, test Tempest access, existing games, game creation, mini-game scoreboards, and GIF/quote rotations. Add a custom domain afterward if desired.

The app reads `DATABASE_URL`, `SECRET_KEY`, `TEMPEST_ADMIN_PASSCODE`, and `APP_ENV` from the deployment environment. Production startup fails if the database URL or session secret is missing. Never put hosted credentials in source files or commit them to GitHub.

Secrets deleted from the current source may still exist in Git history. Rotate the old session key and Tempest code before launch; revoke any previously committed Google/Facebook OAuth credentials too, even though social sign-in has been removed.
