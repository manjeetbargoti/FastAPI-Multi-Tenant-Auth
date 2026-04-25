import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from app.core.config.database import SessionLocal
from app.models.user import User
from app.core.security.security import hash_password

def run():
    db = SessionLocal()

    try:
        email = "admin@platform.com"

        exists = db.query(User).filter(User.email == email).first()

        if exists:
            print("Platform user already exists")
            return
        
        user = User(
            email=email,
            password=hash_password("Admin@123"),
            first_name="Platform",
            last_name="Admin",
            is_super_admin=True,
            is_active=True,
            is_verified=True
        )

        db.add(user)
        db.commit()

        print("Platform user created successfully")
        print("Email:", email)
        print("Password: Admin@123")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
