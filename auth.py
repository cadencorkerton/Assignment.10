"""Registration and login with salted password hashes."""

import hashlib
import re
import secrets

from database import GameDatabase


def _password_hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000
    ).hex()


def authenticate(database: GameDatabase) -> str | None:
    while True:
        print("\n1) Log in   2) Register   Q) Quit")
        choice = input("Choose: ").strip().casefold()
        if choice == "q":
            return None
        if choice not in {"1", "2"}:
            print("Enter 1, 2, or Q.")
            continue

        username = input("Username (3-20 letters, numbers, or _): ").strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
            print("That username is not valid.")
            continue
        username = username.casefold()

        if choice == "2":
            password = input("Password (at least 6 characters; typing is visible): ")
            if len(password) < 6:
                print("Choose a password with at least 6 characters.")
                continue
            confirmation = input("Confirm password (typing is visible): ")
            if password != confirmation:
                print("The passwords did not match.")
                continue
            salt = secrets.token_hex(16)
            if not database.create_account(username, salt, _password_hash(password, salt)):
                print("That username is already registered.")
                continue
            print(f"Account created. Welcome, {username}!")
            return username

        account = database.get_account(username)
        password = input("Password (typing is visible): ")
        if account and secrets.compare_digest(
            _password_hash(password, account["salt"]), account["password_hash"]
        ):
            print(f"Welcome back, {username}!")
            return username
        print("Username or password was incorrect.")
