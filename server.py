# server.py
import os

os.environ.setdefault("DB_BACKEND", "postgres")
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
    app.run(debug=True)
   