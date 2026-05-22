import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask_app.models.user import User


def print_users():
    users = User.list_users() or []
    if not users:
        print("No users found.")
        return

    print("id | email | is_admin | name")
    for row in users:
        full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        print(f"{row['id']} | {row['email']} | {row.get('is_admin')} | {full_name}")


def main():
    parser = argparse.ArgumentParser(description="Promote an existing user to admin")
    parser.add_argument("--email", help="Email of user to promote")
    parser.add_argument("--user-id", type=int, help="User id to promote")
    parser.add_argument("--list-users", action="store_true", help="List users and exit")
    args = parser.parse_args()

    if args.list_users:
        print_users()
        return

    if args.email:
        updated = User.set_admin_by_email(args.email)
        if updated and updated > 0:
            print(f"User with email {args.email} is now admin.")
            return
        print(f"No user found with email {args.email}.")
        return

    if args.user_id:
        updated = User.set_admin_by_id(args.user_id)
        if updated and updated > 0:
            print(f"User with id {args.user_id} is now admin.")
            return
        print(f"No user found with id {args.user_id}.")
        return

    parser.error("Provide --email, --user-id, or --list-users")


if __name__ == "__main__":
    main()
