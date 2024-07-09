from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = 'Keep_It_Low_Key'  # Set to your specified secret key

# Initialize Flask-Bcrypt with the Flask app instance
bcrypt = Bcrypt(app)

# Custom filter to truncate text
@app.template_filter('truncate')
def truncate(s, length):
    return s if len(s) <= length else s[:length] + '...'

# Import routes
from flask_app.controllers import users
from flask_app.controllers import games