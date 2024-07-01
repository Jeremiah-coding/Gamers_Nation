from flask_app.config.mysqlconnection import connectToMySQL
from flask import flash

class Games:
    _db = "videogames_schema"
    
    def __init__(self, data):
        self.id = data["id"]
        self.title = data["title"]
        self.description = data["description"]
        self.system = data["system"]
        self.image_url = data.get("image_url")
        self.user_id = data["user_id"]
        self.created_at = data["created_at"]
        self.updated_at = data["updated_at"]
        
        self.user = {
            "first_name": data["first_name"],
            "last_name": data["last_name"]
        }

    @staticmethod
    def validate_Games(form_data):
        is_valid = True
        if len(form_data["title"].strip()) < 4:
            flash("Game must be at least 4 characters long.", "show")
            is_valid = False
        if len(form_data["description"].strip()) < 10:
            flash("Description of the game must be at least 10 characters long.", "show")
            is_valid = False
        if len(form_data["system"].strip()) < 3:
            flash("System must be at least 3 characters long.", "show")
            is_valid = False
        return is_valid

    @classmethod
    def save(cls, form_data):
        query = """
        INSERT INTO videogames (title, description, `system`, image_url, user_id)
        VALUES (%(title)s, %(description)s, %(system)s, %(image_url)s, %(user_id)s);
        """
        return connectToMySQL(cls._db).query_db(query, form_data)

    @classmethod
    def get_all(cls):
        query = """
        SELECT videogames.*, users.first_name, users.last_name 
        FROM videogames
        JOIN users ON videogames.user_id = users.id;
        """
        results = connectToMySQL(cls._db).query_db(query)
        if results:
            videogames = [cls(row) for row in results]
            return videogames
        return []

    @classmethod
    def get_by_id(cls, id):
        query = """
        SELECT videogames.*, users.first_name, users.last_name 
        FROM videogames
        JOIN users ON videogames.user_id = users.id
        WHERE videogames.id = %(id)s;
        """
        data = {"id": id}
        result = connectToMySQL(cls._db).query_db(query, data)
        if result:
            return cls(result[0])
        return None

    @classmethod
    def get_by_user_id(cls, user_id):
        query = """
        SELECT videogames.*, users.first_name, users.last_name
        FROM videogames
        JOIN users ON videogames.user_id = users.id
        WHERE user_id = %(user_id)s;
        """
        data = {"user_id": user_id}
        results = connectToMySQL(cls._db).query_db(query, data)
        if results:
            videogames = [cls(row) for row in results]
            return videogames
        return []

    @classmethod
    def update(cls, form_data):
        if not cls.validate_Games(form_data):
            return False
        query = """
        UPDATE videogames
        SET title = %(title)s, description = %(description)s, `system` = %(system)s, image_url = %(image_url)s, updated_at = NOW()
        WHERE id = %(id)s AND user_id = %(user_id)s;
        """
        return connectToMySQL(cls._db).query_db(query, form_data)

    @classmethod
    def delete(cls, data):
        query = "DELETE FROM videogames WHERE id = %(id)s;"
        return connectToMySQL(cls._db).query_db(query, data)
