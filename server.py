# server.py
import os

APP_ENV = os.getenv("APP_ENV", "development").lower()

if APP_ENV == "production":
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL must be configured in production.")
    os.environ["DB_BACKEND"] = "postgres"
else:
    local_backend = os.getenv("LOCAL_DB_BACKEND", "postgres").strip().lower()
    if local_backend not in {"postgres", "postgresql", "pg", "sqlite"}:
        raise RuntimeError("LOCAL_DB_BACKEND must be postgres or sqlite.")
    os.environ["DB_BACKEND"] = local_backend
    os.environ.setdefault("PGHOST", "localhost")
    os.environ.setdefault("PGPORT", "15432")
    os.environ.setdefault("PGUSER", "postgres")
    os.environ.setdefault("PGPASSWORD", "postgres")
    os.environ.setdefault("PGDATABASE", "videogames_schema")
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:15432/videogames_schema"
    )

from flask_app import app
if __name__ == "__main__":
    try:
        from flask_app.config.mysqlconnection import connectToMySQL

        if connectToMySQL("videogames_schema").query_db("SELECT 1 AS ready;") is False:
            raise RuntimeError("The database health check failed.")
    except Exception as error:
        raise SystemExit(
            "The configured database is unavailable. Start Docker Desktop and run "
            "scripts/start_dev.ps1 to use the persistent PostgreSQL container. "
            "For isolated local testing only, set LOCAL_DB_BACKEND=sqlite."
        ) from error

    app.run(debug=APP_ENV != "production")
   