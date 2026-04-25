import os
import sys
import getpass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from app.core.config.database import SessionLocal
from app.models.user import User
from app.core.security.security import hash_password


MIN_PASSWORD_LENGTH = 8


def _resolve_password() -> str | None:
    password = os.getenv("PLATFORM_ADMIN_PASSWORD")
    if password:
        return password

    password = getpass.getpass("Enter platform admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match. Aborting.")
        return None
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Password must be at least {MIN_PASSWORD_LENGTH} characters. Aborting.")
        return None
    return password


def run():
    db = SessionLocal()

    try:
        email = os.getenv("PLATFORM_ADMIN_EMAIL", "admin@platform.com")

        exists = db.query(User).filter(User.email == email).first()
        if exists:
            print("Platform user already exists")
            return

        password = _resolve_password()
        if not password:
            return

        user = User(
            email=email,
            password=hash_password(password),
            first_name="Platform",
            last_name="Admin",
            is_super_admin=True,
            is_active=True,
            is_verified=True,
        )

        db.add(user)
        db.commit()

        print("Platform user created successfully")
        print(f"Email: {email}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
