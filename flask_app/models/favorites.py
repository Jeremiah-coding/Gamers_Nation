from flask_app.config.mysqlconnection import connectToMySQL
from flask_app.models.games import Games  # Importing the Games model

class Favorites:
    _db = "videogames_schema"

    @classmethod
    def add(cls, user_id, videogame_id):
        query = "INSERT INTO favorites (user_id, videogame_id) VALUES (%(user_id)s, %(videogame_id)s);"
        data = {"user_id": user_id, "videogame_id": videogame_id}
        result = connectToMySQL(cls._db).query_db(query, data)
        print("Add to Favorites Result:", result)  # Debug statement
        return result

    @classmethod
    def remove(cls, user_id, videogame_id):
        query = "DELETE FROM favorites WHERE user_id = %(user_id)s AND videogame_id = %(videogame_id)s;"
        data = {"user_id": user_id, "videogame_id": videogame_id}
        result = connectToMySQL(cls._db).query_db(query, data)
        print("Remove from Favorites Result:", result)  # Debug statement
        return result
    @classmethod
    def get_favorites_by_user_id(cls, user_id):
        query = """
        SELECT videogames.id, videogames.title, videogames.description, videogames.system
        FROM favorites
        JOIN videogames ON favorites.videogame_id = videogames.id
        WHERE favorites.user_id = %(user_id)s;
        """
        data = {"user_id": user_id}
        results = connectToMySQL(cls._db).query_db(query, data)
        print("Favorites Query Results:", results)  
        if results:
            favorites = []
            for row in results:
                favorite = {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "system": row["system"]
                }
                favorites.append(favorite)
                print("Favorite Added:", favorite)  
            return favorites
        return []