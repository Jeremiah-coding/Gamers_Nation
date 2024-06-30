from flask import render_template, redirect, session, request, flash, make_response
from flask_app import app, bcrypt
from flask_app.models.user import User
from flask_app.models.games import Games
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

@app.get('/')
def index():
    return render_template('index.html')

@app.route("/users/register", methods=['POST'])
def register():
    if not User.validate_register(request.form):
        flash("Invalid registration data", "register")
        return redirect('/')

    potential_user = User.find_by_email(request.form["email"])

    if potential_user:
        flash("Email is in use. Please login.", "register")
        return redirect("/")

    hashed_pw = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
    user_data = {
        "first_name": request.form['first_name'],
        "last_name": request.form['last_name'],
        "email": request.form['email'],
        "password": hashed_pw,
    }
    user_id = User.register(user_data)
    session["user_id"] = user_id
    return redirect("/videogames")

@app.route("/users/login", methods=['POST'])
def login():
    if not User.validate_login(request.form):
        flash("Invalid login data", "login")
        return redirect("/")

    potential_user = User.find_by_email(request.form["email"])
    if not potential_user or not bcrypt.check_password_hash(potential_user.password, request.form['password']):
        flash("Invalid Credentials", "login")
        return redirect("/")

    session['user_id'] = potential_user.id
    return redirect("/videogames")

@app.route("/users/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    response = make_response(redirect("/"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # HTTP 1.1.
    response.headers['Pragma'] = 'no-cache'  # HTTP 1.0.
    response.headers['Expires'] = '0'  # Proxies.
    return response

@app.route("/user/account")
@login_required
@no_cache
def account():
    user_id = session.get('user_id')
    user = User.find_by_user_id(user_id)
    videogames = Games.get_by_user_id(user_id)  # Fetch videogames by user ID
    return render_template("account.html", user=user, videogames=videogames)

@app.route("/user/account/update", methods=["POST"])
@login_required
@no_cache
def update_account():
    user_id = session.get('user_id')
    user = User.find_by_user_id(user_id)
    
    if not user:
        flash("User not found", "error")
        return redirect("/")
    
    form_data = {
        "id": user_id,
        "first_name": request.form["first_name"],
        "last_name": request.form["last_name"],
        "email": request.form["email"]
    }
    
    if not User.validate_update(form_data):
        return redirect("/user/account")
    
    User.update_user(form_data)
    flash("Account updated successfully", "success")
    return redirect("/user/account")

@app.route("/user/account/delete/<int:videogames_id>")
@login_required
@no_cache
def delete_user_videogames(videogames_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect("/")
    
    videogames = Games.get_by_id(videogames_id)
    if not videogames or videogames.user_id != user_id:
        flash("You are not authorized to delete this videogame", "error")
    else:
        Games.delete({"id": videogames_id})
        flash("Videogame deleted successfully", "success")
    
    return redirect("/user/account")
