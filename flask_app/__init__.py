from flask import Flask
from flask_bcrypt import Bcrypt
import re
from urllib.parse import urlparse, parse_qs

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

    cleaned = url.strip()
    parsed = urlparse(cleaned)
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        short_id = parsed.path.lstrip('/').split('/')[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", short_id):
            return short_id

    if "youtube.com" in host or "youtube-nocookie.com" in host:
        query_video_id = parse_qs(parsed.query).get("v", [""])[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", query_video_id):
            return query_video_id

        path_parts = [part for part in parsed.path.split('/') if part]
        for i, part in enumerate(path_parts):
            if part in {"embed", "shorts", "v"} and i + 1 < len(path_parts):
                candidate = path_parts[i + 1]
                if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
                    return candidate

    match = re.search(r"([A-Za-z0-9_-]{11})", cleaned)
    if match:
        return match.group(1)

    return ''

# Import routes
from flask_app.controllers import users
from flask_app.controllers import games
