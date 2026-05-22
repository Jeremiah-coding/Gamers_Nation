import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask_app import bcrypt
from flask_app.models.user import User


def main():
    parser = argparse.ArgumentParser(description="Create or promote an admin user")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--first-name", default="Admin", help="First name for new user")
    parser.add_argument("--last-name", default="User", help="Last name for new user")
    parser.add_argument("--password", default="Admin12345!", help="Password for new user")
    args = parser.parse_args()

    existing = User.find_by_email(args.email)
    if existing:
        User.set_admin_by_email(args.email)
        print(f"Existing user {args.email} promoted to admin.")
        return

    hashed_pw = bcrypt.generate_password_hash(args.password).decode("utf-8")
    user_id = User.register(
        {
            "first_name": args.first_name,
            "last_name": args.last_name,
            "email": args.email,
            "password": hashed_pw,
            "avatar_url": "/static/images/Shadow.gif",
        }
    )
    User.set_admin_by_id(user_id)
    print(f"Created admin user {args.email} with id {user_id}.")


if __name__ == "__main__":
    main()
