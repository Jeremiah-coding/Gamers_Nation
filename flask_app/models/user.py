import re
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
        self.password = data["password"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]

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
        is_valid = True
        if len(form_data["first_name"].strip()) < 2:
            flash("First name must be at least two characters", "update")
            is_valid = False
        if len(form_data["last_name"].strip()) < 2:
            flash("Last name must be at least two characters", "update")
            is_valid = False
        if not EMAIL_REGEX.match(form_data["email"]):
            flash("Email address is invalid.", "update")
            is_valid = False
        return is_valid

    @classmethod
    def register(cls, user_data):
        query = """
        INSERT INTO users (first_name, last_name, email, password)
        VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password)s);
        """
        return connectToMySQL(cls._db).query_db(query, user_data)

    @classmethod
    def find_by_email(cls, email):
        query = """
        SELECT * FROM users WHERE email = %(email)s;
        """
        data = {"email": email}
        results = connectToMySQL(cls._db).query_db(query, data)
        if results:
            return cls(results[0])
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
        SET first_name = %(first_name)s, last_name = %(last_name)s, email = %(email)s
        WHERE id = %(id)s;
        """
        return connectToMySQL(cls._db).query_db(query, form_data)
