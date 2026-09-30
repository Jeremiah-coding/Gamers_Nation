from flask import render_template, request, redirect, session, flash, url_for, make_response
from flask_app import app
from flask_app.models.user import User
from flask_app.models.games import Games
from functools import wraps
import hmac
import os

def visitor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Enter your first name to continue.", "visitor")
            return redirect(url_for('index'))
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

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/users/enter')
def enter_as_visitor():
    first_name = request.form.get('first_name', '').strip()
    if len(first_name) < 2 or len(first_name) > 50:
        flash('Your name must be between 2 and 50 characters long.', 'visitor')
        return redirect(url_for('index'))

    if first_name.casefold() == 'tempest':
        configured_passcode = os.environ.get('TEMPEST_ADMIN_PASSCODE', '135047')
        submitted_passcode = request.form.get('admin_passcode', '')
        if not configured_passcode or not hmac.compare_digest(submitted_passcode, configured_passcode):
            flash('That superuser name is reserved. Enter the valid superuser passcode or choose another name.', 'visitor')
            return redirect(url_for('index'))

        user = User.find_superuser_by_first_name('Tempest')
        if not user:
            if User.find_by_first_name('Tempest'):
                flash('The Tempest superuser account needs administrator setup. Please choose another name for now.', 'visitor')
                return redirect(url_for('index'))
            user_id = User.create_visitor('Tempest', is_admin=True)
        else:
            user_id = user.id
        visitor_name = 'Tempest'
    else:
        if User.find_by_first_name(first_name):
            flash('That name is already in use. Please try another name.', 'visitor')
            return redirect(url_for('index'))
        user_id = User.create_visitor(first_name)
        visitor_name = first_name

    if not user_id:
        flash('We could not open your visitor session. Please try again.', 'visitor')
        return redirect(url_for('index'))

    session.clear()
    session['user_id'] = user_id
    session['visitor_mode'] = True
    session['visitor_name'] = visitor_name
    return redirect(url_for('all_Games'))

@app.get('/users/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('index')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/user/account")
@visitor_required
@no_cache
def account():
    user_id = session.get('user_id')
    user = User.find_by_user_id(user_id)
    videogames = Games.get_by_user_id(user_id)  # Fetch videogames by user ID
    return render_template("account.html", user=user, videogames=videogames)

@app.route("/user/account/update", methods=["POST"])
@visitor_required
@no_cache
def update_account():
    user_id = session.get('user_id')
    user = User.find_by_user_id(user_id)

    if not user:
        flash("User not found", "error")
        return redirect("/")

    first_name = request.form.get("first_name", "").strip()
    if user.is_admin:
        if first_name.casefold() != "tempest":
            flash("The Tempest superuser name cannot be changed.", "update")
            return redirect("/user/account")
        first_name = "Tempest"
    if len(first_name) < 2 or len(first_name) > 50:
        flash("Your name must be between 2 and 50 characters long.", "update")
        return redirect("/user/account")
    existing_user = User.find_by_first_name(first_name)
    if existing_user and existing_user.id != user_id:
        flash("That name is already in use. Please try another name.", "update")
        return redirect("/user/account")

    form_data = {
        "id": user_id,
        "first_name": first_name,
        "avatar_url": request.form.get("avatar_url", user.avatar_url)
    }

    User.update_user(form_data)
    session["visitor_name"] = first_name
    flash("Account updated successfully", "success")
    return redirect("/user/account")

@app.route("/user/account/delete/<int:videogames_id>")
@visitor_required
@no_cache
def delete_user_videogames(videogames_id):
    user_id = session.get('user_id')
    current_user = User.find_by_user_id(user_id)
    if not current_user or not current_user.is_admin:
        flash('Only the Tempest superuser can delete games.', 'error')
        return redirect("/")

    videogames = Games.get_by_id(videogames_id)
    if videogames:
        Games.delete({"id": videogames_id})
        flash("Videogame deleted successfully", "success")
    else:
        flash("Videogame not found", "error")

    return redirect("/user/account")
# Route to initiate account deletion (shows confirmation message)
@app.post("/user/account/delete")
@visitor_required
@no_cache
def delete_account():
    user_id = session.get('user_id')
    user = User.find_by_user_id(user_id)

    if not user:
        flash("User not found", "error")
        session.clear()
        return redirect(url_for('index'))

    if user.is_admin:
        flash("The Tempest superuser account cannot be deleted.", "error")
        return redirect("/user/account")

    if User.delete_user(user_id) is False:
        flash("Your account could not be deleted. Please try again.", "error")
        return redirect("/user/account")

    session.clear()
    flash("Your account has been deleted successfully.", "success")
    return redirect(url_for('index'))

