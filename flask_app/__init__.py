from flask import Flask
from flask_bcrypt import Bcrypt
import re

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = 'Keep_It_Low_Key'

# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)

# Custom filter to truncate text
@app.template_filter('truncate')
def truncate(s, length):
    return s if len(s) <= length else s[:length] + '...'

# Custom filter to extract YouTube video ID
@app.template_filter('extract_youtube_id')
def extract_youtube_id(url):
    """
    Extracts the YouTube video ID from various possible YouTube URL formats.
    """
    if not url:
        return ''
    regex = r"(?:v=|\/embed\/|youtu\.be\/)([A-Za-z0-9_-]{11})"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return ''

# Import routes
from flask_app.controllers import users
from flask_app.controllers import games
