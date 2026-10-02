import re
from uuid import uuid4
from flask import flash
from flask_app.config.mysqlconnection import connectToMySQL

# Regular expression for email validation
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

class User:
    _db = "videogames_schema"

    def __init__(self, data):
        self.id = data["id"]
        self.first_name = data["first_name"]
        self.last_name = data["last_name"]
        self.email = data["email"]
        self.is_admin = bool(data.get("is_admin", 0))
        self.password = data.get("password")
        self.google_id = data.get("google_id")
        self.facebook_id = data.get("facebook_id")
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        self.avatar_url = data.get("avatar_url", "/static/images/Shadow.gif")  # Default to shadow GIF

    @staticmethod
    def validate_register(form_data):
        is_valid = True
        if len(form_data["first_name"].strip()) == 0:
            flash("Please enter first name.", "register")
            is_valid = False
        elif len(form_data["first_name"].strip()) < 2:
            flash("First name must be at least two characters", "register")
            is_valid = False
        if len(form_data["last_name"].strip()) == 0:
            flash("Please enter last name.", "register")
            is_valid = False
        elif len(form_data["last_name"].strip()) < 2:
            flash("Last name must be at least two characters", "register")
            is_valid = False
        if len(form_data["email"].strip()) == 0:
            flash("Please enter email.", "register")
            is_valid = False
        elif not EMAIL_REGEX.match(form_data["email"]):
            flash("Email address is invalid.", "register")
            is_valid = False
        if len(form_data["password"].strip()) == 0:
            flash("Please enter password.", "register")
            is_valid = False
        elif len(form_data["password"].strip()) < 8:
            flash("Password must be at least eight characters", "register")
            is_valid = False
        elif form_data["password"] != form_data["confirm_password"]:
            flash("Passwords do not match. Try again.", "register")
            is_valid = False
        return is_valid

    @staticmethod
    def validate_login(form_data):
        is_valid = True
        if len(form_data["email"].strip()) == 0:
            flash("Please enter email.", "login")
            is_valid = False
        elif not EMAIL_REGEX.match(form_data["email"]):
            flash("Email address is invalid.", "login")
            is_valid = False
        if len(form_data["password"].strip()) == 0:
            flash("Please enter password.", "login")
            is_valid = False
        elif len(form_data["password"].strip()) < 8:
            flash("Password must be at least eight characters", "login")
            is_valid = False
        return is_valid

    @staticmethod
    def validate_update(form_data):
        first_name = form_data.get("first_name", "").strip()
        if not 2 <= len(first_name) <= 50:
            flash("Your name must be between 2 and 50 characters long.", "update")
            return False
        return True

    @classmethod
    def register(cls, user_data):
        query = """
        INSERT INTO users (first_name, last_name, email, password, avatar_url)
        VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s, %(avatar_url)s);
        """
        return connectToMySQL(cls._db).query_db(query, user_data)

    @classmethod
    def find_by_first_name(cls, first_name):
        query = "SELECT * FROM users WHERE LOWER(first_name) = LOWER(%(first_name)s) ORDER BY id LIMIT 1;"
        results = connectToMySQL(cls._db).query_db(query, {"first_name": first_name})
        return cls(results[0]) if results else None

    @classmethod
    def find_superuser_by_first_name(cls, first_name):
        query = "SELECT * FROM users WHERE LOWER(first_name) = LOWER(%(first_name)s) AND is_admin = TRUE ORDER BY id LIMIT 1;"
        results = connectToMySQL(cls._db).query_db(query, {"first_name": first_name})
        return cls(results[0]) if results else None

    @classmethod
    def create_visitor(cls, first_name, is_admin=False, pin_hash=None):
        query = """
        INSERT INTO users (first_name, last_name, email, password, avatar_url, is_admin)
        VALUES (%(first_name)s, '', %(email)s, %(password)s, %(avatar_url)s, %(is_admin)s);
        """
        data = {
            "first_name": first_name,
            "email": f"visitor-{uuid4().hex}@gamersnation.local",
            "password": pin_hash,
            "avatar_url": "/static/images/Shadow.gif",
            "is_admin": is_admin,
        }
        return connectToMySQL(cls._db).query_db(query, data)

    @classmethod
    def set_visitor_pin(cls, user_id, pin_hash):
        query = """
        UPDATE users
        SET password = %(password)s, updated_at = NOW()
        WHERE id = %(id)s AND password IS NULL AND is_admin = FALSE;
        """
        return connectToMySQL(cls._db).query_db(query, {"id": user_id, "password": pin_hash})

    @classmethod
    def find_by_email(cls, email):
        query = """
        SELECT * FROM users WHERE email = %(email)s;
        """
        data = {"email": email}
        results = connectToMySQL(cls._db).query_db(query, data)
        if results:  # Check if results are non-empty
            return cls(results[0])  # Return User object if a match is found
        return None

    @classmethod
    def find_by_user_id(cls, user_id):
        query = """
        SELECT * FROM users WHERE id = %(user_id)s;
        """
        data = {"user_id": user_id}
        results = connectToMySQL(cls._db).query_db(query, data)
        if results:
            return cls(results[0])
        return None

    @classmethod
    def update_user(cls, form_data):
        query = """
        UPDATE users
        SET first_name = %(first_name)s, avatar_url = %(avatar_url)s
        WHERE id = %(id)s;
        """
        return connectToMySQL(cls._db).query_db(query, form_data)

    @classmethod
    def delete_user(cls, user_id):
        user = cls.find_by_user_id(user_id)
        if not user or user.is_admin:
            return False

        owned_games = connectToMySQL(cls._db).query_db(
            "SELECT COUNT(*) AS game_count FROM videogames WHERE user_id = %(user_id)s;",
            {"user_id": user_id},
        )
        if owned_games and owned_games[0]["game_count"]:
            admin = cls.find_superuser_by_first_name("Tempest")
            if not admin:
                return False
            transfer_result = connectToMySQL(cls._db).query_db(
                "UPDATE videogames SET user_id = %(admin_id)s WHERE user_id = %(user_id)s;",
                {"admin_id": admin.id, "user_id": user_id},
            )
            if transfer_result is False:
                return False

        query = "DELETE FROM users WHERE id = %(id)s;"
        data = {"id": user_id}
        return connectToMySQL(cls._db).query_db(query, data)

    @classmethod
    def set_admin_by_email(cls, email):
        query = "UPDATE users SET is_admin = TRUE WHERE email = %(email)s;"
        data = {"email": email}
        return connectToMySQL(cls._db).query_db(query, data)

    @classmethod
    def set_admin_by_id(cls, user_id):
        query = "UPDATE users SET is_admin = TRUE WHERE id = %(id)s;"
        data = {"id": user_id}
        return connectToMySQL(cls._db).query_db(query, data)

    @classmethod
    def list_users(cls):
        query = "SELECT id, first_name, last_name, email, is_admin FROM users ORDER BY id;"
        return connectToMySQL(cls._db).query_db(query)
