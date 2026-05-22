import os
import re
import sqlite3

from psycopg import connect as pg_connect
from psycopg.rows import dict_row


class SQLiteConnection:
    _db_initialized = False

    def __init__(self, db_name):
        self.db_name = db_name
        self.db_path = os.getenv("SQLITE_DB_PATH") or self._default_db_path()
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self._ensure_schema()

    def _default_db_path(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, f"{self.db_name}.db")

    @classmethod
    def _ensure_schema(cls):
        if cls._db_initialized:
            return

        schema_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                is_admin INTEGER NOT NULL DEFAULT 0,
                password TEXT,
                avatar_url TEXT,
                google_id TEXT,
                facebook_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS videogames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                system TEXT NOT NULL,
                image_url TEXT,
                video_url TEXT,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                videogame_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (videogame_id) REFERENCES videogames(id) ON DELETE CASCADE,
                UNIQUE(user_id, videogame_id)
            );
            """,
        ]

        conn = sqlite3.connect(os.getenv("SQLITE_DB_PATH") or cls._default_class_db_path())
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            for statement in schema_statements:
                cursor.execute(statement)
            cursor.execute("PRAGMA table_info(users);")
            user_columns = {row[1] for row in cursor.fetchall()}
            if "is_admin" not in user_columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;")
            conn.commit()
            cls._db_initialized = True
        finally:
            conn.close()

    @staticmethod
    def _default_class_db_path():
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "videogames_schema.db")

    @staticmethod
    def _normalize_query(query):
        normalized = query.replace("NOW()", "CURRENT_TIMESTAMP")
        normalized = normalized.replace("`", '"')
        normalized = re.sub(r"%\((\w+)\)s", r":\1", normalized)
        return normalized

    def query_db(self, query: str, data: dict = None):
        cursor = self.connection.cursor()
        try:
            normalized_query = self._normalize_query(query)
            payload = data or {}
            print("Running Query:", normalized_query)
            cursor.execute(normalized_query, payload)

            query_type = normalized_query.strip().split()[0].lower() if normalized_query.strip() else ""
            if query_type == "insert":
                self.connection.commit()
                return cursor.lastrowid
            if query_type == "select":
                return [dict(row) for row in cursor.fetchall()]

            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            print("Something went wrong", e)
            return False
        finally:
            cursor.close()
            self.connection.close()


class PostgreSQLConnection:
    _db_initialized = False

    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = pg_connect(self._build_dsn(), row_factory=dict_row)
        self._ensure_schema()

    def _build_dsn(self):
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "postgres")
        dbname = os.getenv("PGDATABASE", self.db_name)
        return f"host={host} port={port} user={user} password={password} dbname={dbname}"

    @classmethod
    def _ensure_schema(cls):
        if cls._db_initialized:
            return

        schema_statements = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                password TEXT,
                avatar_url TEXT,
                google_id TEXT,
                facebook_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS videogames (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                system TEXT NOT NULL,
                image_url TEXT,
                video_url TEXT,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_videogames_user FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                user_id INTEGER NOT NULL,
                videogame_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_favorites_game FOREIGN KEY (videogame_id) REFERENCES videogames(id) ON DELETE CASCADE,
                CONSTRAINT favorites_unique_user_game UNIQUE(user_id, videogame_id)
            );
            """,
        ]

        conn = pg_connect(cls._class_dsn())
        try:
            with conn.cursor() as cursor:
                for statement in schema_statements:
                    cursor.execute(statement)
                cursor.execute(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = 'is_admin';
                    """
                )
                if cursor.fetchone() is None:
                    cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;")
            conn.commit()
            cls._db_initialized = True
        finally:
            conn.close()

    @staticmethod
    def _class_dsn():
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        host = os.getenv("PGHOST", "localhost")
        port = os.getenv("PGPORT", "5432")
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "postgres")
        dbname = os.getenv("PGDATABASE", "videogames_schema")
        return f"host={host} port={port} user={user} password={password} dbname={dbname}"

    @staticmethod
    def _normalize_query(query):
        normalized = query.replace("`", '"')
        return normalized

    def query_db(self, query: str, data: dict = None):
        try:
            normalized_query = self._normalize_query(query)
            payload = data or {}
            query_type = normalized_query.strip().split()[0].lower() if normalized_query.strip() else ""
            normalized_query = normalized_query.strip()

            if query_type == "insert" and "returning" not in normalized_query.lower():
                normalized_query = normalized_query.rstrip(";") + " RETURNING id;"

            print("Running Query:", normalized_query)
            with self.connection.cursor() as cursor:
                cursor.execute(normalized_query, payload)

                if query_type == "insert":
                    inserted = cursor.fetchone()
                    self.connection.commit()
                    return inserted["id"] if inserted else None
                if query_type == "select":
                    return cursor.fetchall()

                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            print("Something went wrong", e)
            return False
        finally:
            self.connection.close()


def connectToMySQL(db):
    backend = os.getenv("DB_BACKEND", "sqlite").strip().lower()
    if backend in {"postgres", "postgresql", "pg"}:
        return PostgreSQLConnection(db)
    return SQLiteConnection(db)