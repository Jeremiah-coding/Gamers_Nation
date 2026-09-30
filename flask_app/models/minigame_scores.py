from flask_app.config.mysqlconnection import connectToMySQL


GAMES = {
    "snake": "Neon Snake",
    "memory": "Memory Match",
    "click-rush": "Click Rush",
    "frogger": "Frogger Dash",
    "whack-a-mole": "Whack-a-Mole",
    "pacman": "Pac-Man Maze",
}


class MinigameScores:
    _db = "videogames_schema"

    @classmethod
    def submit(cls, game_key, user_id, score):
        query = """
        INSERT INTO minigame_scores (game_key, user_id, score)
        VALUES (%(game_key)s, %(user_id)s, %(score)s);
        """
        return connectToMySQL(cls._db).query_db(
            query,
            {"game_key": game_key, "user_id": user_id, "score": score},
        )

    @classmethod
    def top_five(cls, game_key):
        query = """
        SELECT minigame_scores.score, users.first_name AS player_name, minigame_scores.created_at
        FROM minigame_scores
        JOIN users ON minigame_scores.user_id = users.id
        WHERE minigame_scores.game_key = %(game_key)s
        ORDER BY minigame_scores.score DESC, minigame_scores.created_at ASC, minigame_scores.id ASC
        LIMIT 5;
        """
        return connectToMySQL(cls._db).query_db(query, {"game_key": game_key}) or []
