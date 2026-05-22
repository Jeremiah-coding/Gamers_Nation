from flask import render_template, request, redirect, session, flash, make_response, url_for, jsonify
from flask_app import app
from flask_app.models.games import Games
from flask_app.models.user import User
from flask_app.models.favorites import Favorites
from functools import wraps
import requests
from urllib.parse import urlparse, parse_qs, unquote


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".avif")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in first", "error")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return no_cache_view


def _looks_like_direct_image(url):
    parsed = urlparse(url)
    path = (parsed.path or "").lower()
    if any(path.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return True

    query = parse_qs(parsed.query)
    format_hint = (query.get("format", [""])[0] or "").lower()
    if format_hint in {"jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "avif"}:
        return True
    return False


def _is_valid_image_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.head(url, allow_redirects=True, timeout=6, headers=headers)
        content_type = (response.headers.get("Content-Type") or "").lower()
        if response.ok and content_type.startswith("image/"):
            return True
        if response.status_code in {403, 405} or not content_type:
            response = requests.get(url, allow_redirects=True, timeout=6, headers=headers, stream=True)
            content_type = (response.headers.get("Content-Type") or "").lower()
            if response.ok and content_type.startswith("image/"):
                return True
    except requests.RequestException:
        pass

    return _looks_like_direct_image(url)


def _candidate_image_urls(url):
    cleaned = url.strip()
    parsed = urlparse(cleaned)
    host = parsed.netloc.lower()
    query = parse_qs(parsed.query)

    candidates = [cleaned]

    for key in ("mediaurl", "imgurl", "url", "u"):
        wrapped = query.get(key, [None])[0]
        if wrapped:
            candidates.append(unquote(wrapped))

    if "google." in host and parsed.path == "/imgres":
        imgurl = query.get("imgurl", [None])[0]
        if imgurl:
            candidates.append(unquote(imgurl))

    if "bing.com" in host and parsed.path.startswith("/images/search"):
        media_url = query.get("mediaurl", [None])[0]
        if media_url:
            candidates.append(unquote(media_url))

    unique_candidates = []
    for candidate in candidates:
        if candidate and candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def normalize_image_url(url):
    if not url:
        return None

    for candidate in _candidate_image_urls(url):
        if _is_valid_image_url(candidate):
            return candidate
    return None


def normalize_video_url(url):
    if not url:
        return None
    return url.strip()


CLIENT_ID = 'rctfju3cojvlxxl2irml3308q0s9gg'
REDIRECT_URI = 'HTTP://localhost:5000/oauth/callback'



@app.route('/videogames/igdb/login')
def igdb_login():
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&response_type=token&scope=user:read:email"
    )
    return redirect(auth_url)
@app.route('/oauth/callback')
def oauth_callback():
    # Handle the callback from Twitch
    # For example, you could render the igdb_games.html template directly
    return render_template('database.html')
@app.route('/fetch-games')
def fetch_games():
    access_token = request.args.get('access_token')
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': 'rctfju3cojvlxxl2irml3308q0s9gg',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'text/plain'
    }
    body = 'fields name,summary,cover.url,first_release_date,platforms.name,rating; sort rating desc; limit 10;'
    response = requests.post(url, headers=headers, data=body)
    return jsonify(response.json())
@app.route('/search-games')
def search_games():
    access_token = request.args.get('access_token')
    query = request.args.get('query')
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': 'rctfju3cojvlxxl2irml3308q0s9gg',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'text/plain'
    }
    
    # Include the search query in the request body
    body = f"""
    search "{query}";
    fields name,summary,cover.url,first_release_date,platforms.name,rating;
    limit 10;
    """
    
    response = requests.post(url, headers=headers, data=body)
    return jsonify(response.json())
@app.route('/fetch-top-games')
def fetch_top_games():
    access_token = request.args.get('access_token')
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': 'rctfju3cojvlxxl2irml3308q0s9gg',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'text/plain'
    }
    
    # Request top-rated games
    body = """
    fields name,summary,cover.url,first_release_date,platforms.name,rating;
    sort rating desc;
    limit 10;
    """
    
    response = requests.post(url, headers=headers, data=body)
    return jsonify(response.json())
@app.route('/filter-games')
def filter_games():
    access_token = request.args.get('access_token')
    genre_name = request.args.get('genre')

    # Map genre names to IGDB genre IDs (example IDs, replace with actual IDs)
    genre_map = {
        "Strategy": 15,
        "Fighting": 4,
        "Adventure": 31,
        "Platform": 9,
        "RPG": 12,
        "MOBA": 36,
        "Racing": 10,
        "Family": 7,
        "Music": 7,
         }

    genre_id = genre_map.get(genre_name)
    
    if not genre_id:
        return jsonify([])

    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': 'rctfju3cojvlxxl2irml3308q0s9gg',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'text/plain'
    }
    
    # Fetch top 15 games in the selected genre
    body = f"""
    fields name,summary,cover.url,first_release_date,platforms.name,rating;
    where genres = ({genre_id});
    sort rating desc;
    limit 15;
    """
    
    response = requests.post(url, headers=headers, data=body)
    return jsonify(response.json())


@app.route("/study")
@login_required
def study_page():
    return render_template("study.html")


@app.route("/videogames")
@login_required
@no_cache
def all_Games():
    user_id = session.get('user_id')
    user = User.find_by_user_id(user_id)
    videogames = Games.get_all()
    favorites = Favorites.get_favorites_by_user_id(user_id)
    added_to_favorites = request.args.get('added_to_favorites')
    removed_from_favorites = request.args.get('removed_from_favorites')
    created_success = request.args.get('created_success')
    updated_success = request.args.get('updated_success')
    return render_template("dashboard.html", videogames=videogames, user=user, favorites=favorites, added_to_favorites=added_to_favorites, removed_from_favorites=removed_from_favorites, created_success=created_success, updated_success=updated_success, current_user_id=user_id, is_admin=user.is_admin)

@app.route("/videogames/form")
@login_required
@no_cache
def videogame_form():
    return render_template("videogame_form.html")

@app.route("/videogames/<int:videogames_id>")
@login_required
@no_cache
def show_videogame(videogames_id):
    videogames = Games.get_by_id(videogames_id)
    if not videogames:
        flash("Videogame not found", "error")
        return redirect("/videogames")
    return render_template("videogame.html", videogame=videogames)

@app.route("/videogames/save", methods=["POST"])
@login_required
@no_cache
def save_videogame():
    user_id = session.get('user_id')
    raw_image_url = request.form.get("image_url")
    normalized_image_url = normalize_image_url(raw_image_url)
    if raw_image_url and not normalized_image_url:
        flash("Please provide a direct image link (Google/Bing/Reddit wrappers are supported when detectable).", "show")
        return redirect("/videogames/form")

    form_data = {
        "title": request.form["title"],
        "description": request.form["description"],
        "system": request.form["system"],
        "image_url": normalized_image_url,
        "video_url": normalize_video_url(request.form.get("video_url")),
        "user_id": user_id
    }

    if not Games.validate_Games(form_data):
        return redirect("/videogames/form")

    Games.save(form_data)
    return redirect(url_for('all_Games', created_success=True))

@app.route("/videogames/<int:videogames_id>/edit")
@login_required
@no_cache
def edit_videogame_form(videogames_id):
    videogame = Games.get_by_id(videogames_id)
    current_user = User.find_by_user_id(session.get('user_id'))
    if not videogame or not current_user:
        flash("Videogame not found", "error")
        return redirect("/videogames")
    if not current_user.is_admin and videogame.user_id != current_user.id:
        flash("You are not authorized to edit this Videogame", "error")
        return redirect("/videogames")
    return render_template("edit.html", videogame=videogame)

@app.route("/videogames/<int:videogames_id>/update", methods=["POST"])
@login_required
@no_cache
def update_videogame(videogames_id):
    user_id = session.get('user_id')
    current_user = User.find_by_user_id(user_id)
    videogame = Games.get_by_id(videogames_id)
    if not current_user or not videogame:
        flash("Videogame not found", "error")
        return redirect("/videogames")
    if not current_user.is_admin and videogame.user_id != current_user.id:
        flash("You are not authorized to update this Videogame", "error")
        return redirect("/videogames")

    raw_image_url = request.form.get("image_url")
    normalized_image_url = normalize_image_url(raw_image_url)
    if raw_image_url and not normalized_image_url:
        flash("Please provide a direct image link (Google/Bing/Reddit wrappers are supported when detectable).", "show")
        return redirect(f"/videogames/{videogames_id}/edit")

    form_data = {
        "id": videogames_id,
        "title": request.form["title"],
        "description": request.form["description"],
        "system": request.form["system"],
        "image_url": normalized_image_url,
        "video_url": normalize_video_url(request.form.get("video_url")),
        "user_id": user_id,
        "is_admin": current_user.is_admin
    }

    if not Games.validate_Games(form_data):
        return redirect(f"/videogames/{videogames_id}/edit")

    Games.update(form_data)
    if request.referrer and 'account' in request.referrer:
        return redirect(url_for('user_account', updated_success=True))
    return redirect(url_for('all_Games', updated_success=True))

@app.route("/videogames/<int:videogames_id>/delete", methods=["POST"])
@login_required
@no_cache
def delete_videogame(videogames_id):
    user_id = session.get('user_id')
    current_user = User.find_by_user_id(user_id)
    videogames = Games.get_by_id(videogames_id)
    if not videogames or not current_user:
        flash("Videogame not found", "error")
        return redirect("/videogames")
    if not current_user.is_admin and videogames.user_id != user_id:
        flash("You are not authorized to delete this Videogame", "error")
        return redirect("/videogames")
    Games.delete({"id": videogames_id})
    flash("Videogame deleted successfully", "success")
    if request.referrer and 'account' in request.referrer:
        return redirect(url_for('user_account', deleted_success=True))
    return redirect(url_for('all_Games', deleted_success=True))

@app.route("/favorites/add/<int:videogame_id>")
@login_required
def add_to_favorites(videogame_id):
    user_id = session['user_id']
    Favorites.add(user_id, videogame_id)
    return redirect(url_for('all_Games', added_to_favorites=True))

@app.route("/favorites/remove/<int:videogame_id>")
@login_required
def remove_from_favorites(videogame_id):
    user_id = session['user_id']
    Favorites.remove(user_id, videogame_id)
    return redirect(url_for('all_Games', removed_from_favorites=True))

@app.route("/user/account")
@login_required
def user_account():
    user_id = session['user_id']
    user = User.find_by_user_id(user_id)
    videogames = Games.get_by_user_id(user_id)
    updated_success = request.args.get('updated_success')
    deleted_success = request.args.get('deleted_success')
    return render_template("account.html", user=user, videogames=videogames, updated_success=updated_success, deleted_success=deleted_success)
