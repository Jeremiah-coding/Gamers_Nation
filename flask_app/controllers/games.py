from flask import render_template, request, redirect, session, flash, make_response, url_for
from flask_app import app
from flask_app.models.games import Games
from flask_app.models.user import User
from flask_app.models.favorites import Favorites
from functools import wraps

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
    return render_template("dashboard.html", videogames=videogames, user=user, favorites=favorites, added_to_favorites=added_to_favorites, removed_from_favorites=removed_from_favorites, created_success=created_success, updated_success=updated_success)

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
    return render_template("videogame.html", videogames=videogames)

@app.route("/videogames/save", methods=["POST"])
@login_required
@no_cache
def save_videogame():
    user_id = session.get('user_id')
    form_data = {
        "title": request.form["title"],
        "description": request.form["description"],
        "system": request.form["system"],
        "image_url": request.form["image_url"] if request.form["image_url"] else None,  # Add image_url handling
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
    if not videogame or videogame.user_id != session.get('user_id'):
        flash("You are not authorized to edit this Videogame", "error")
        return redirect("/videogames")
    return render_template("edit.html", videogame=videogame)

@app.route("/videogames/<int:videogames_id>/update", methods=["POST"])
@login_required
@no_cache
def update_videogame(videogames_id):
    user_id = session.get('user_id')
    form_data = {
        "id": videogames_id,
        "title": request.form["title"],
        "description": request.form["description"],
        "system": request.form["system"],
        "image_url": request.form["image_url"] if request.form["image_url"] else None,  # Add image_url handling
        "user_id": user_id
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
    videogames = Games.get_by_id(videogames_id)
    if not videogames or videogames.user_id != user_id:
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
