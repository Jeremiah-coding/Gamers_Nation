from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)  # Initialize Flask-Bcrypt with the Flask app instance

# Custom filter to truncate text
@app.template_filter('truncate')
def truncate(s, length):
    return s if len(s) <= length else s[:length] + '...'

# Import and register blueprints or routes
from flask_app.controllers import users
from flask_app.controllers import games

