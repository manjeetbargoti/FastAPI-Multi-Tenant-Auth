"""
Default-tenant bootstrap.

Idempotently creates:
  - one tenant (name from SEED_TENANT_NAME, default "default")
  - one tenant-admin user (email from SEED_TENANT_ADMIN_EMAIL)
  - the user's UserTenant membership row
  - the user's UserRole grant for the SYSTEM admin role

PRE-REQUISITE: the system `admin` role must already exist. Run
`python app/cli/system_seed.py` first if it's missing — this script will
exit cleanly without writing anything in that case.

    python app/cli/tenant_seed.py
"""

import os
import sys
import getpass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from app.core.config.database import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_tenant import UserTenant
from app.models.user_role import UserRole
from app.repositories.role_repo import RoleRepo
from app.core.security.security import hash_password


TENANT_NAME = os.getenv("SEED_TENANT_NAME", "default")
TENANT_ADMIN_EMAIL = os.getenv("SEED_TENANT_ADMIN_EMAIL", "admin@tenant.com")
SYSTEM_ADMIN_ROLE_NAME = "admin"
MIN_PASSWORD_LENGTH = 8


def _resolve_password() -> str | None:
    password = os.getenv("SEED_TENANT_ADMIN_PASSWORD")
    if password:
        return password

    password = getpass.getpass("Enter tenant admin password: ")
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
        # Pre-flight: the SYSTEM admin role MUST exist before we provision
        # a tenant. Bail BEFORE touching anything else if it's missing.
        admin_role = RoleRepo(db=db).get_system_role(name=SYSTEM_ADMIN_ROLE_NAME)
        if admin_role is None:
            print(
                f"ERROR: system role '{SYSTEM_ADMIN_ROLE_NAME}' is not seeded. "
                "Run `python app/cli/system_seed.py` first."
            )
            return

        existing_tenant = db.query(Tenant).filter(Tenant.name == TENANT_NAME).first()
        existing_user = db.query(User).filter(User.email == TENANT_ADMIN_EMAIL).first()

        # Resolve the password BEFORE writing anything if we'll need it.
        # Failing here leaves the DB completely untouched.
        if existing_user is None:
            password = _resolve_password()
            if not password:
                db.rollback()
                return
        else:
            password = None

        if existing_tenant is None:
            tenant = Tenant(name=TENANT_NAME)
            db.add(tenant)
            db.flush()
            print(f"[+] Tenant created: {TENANT_NAME}")
        else:
            tenant = existing_tenant
            print(f"[=] Tenant already exists: {TENANT_NAME}")

        if existing_user is None:
            user = User(
                email=TENANT_ADMIN_EMAIL,
                password=hash_password(password),
                first_name="Tenant",
                last_name="Admin",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.flush()
            print(f"[+] Tenant admin user created: {TENANT_ADMIN_EMAIL}")
        else:
            user = existing_user
            print(f"[=] Tenant admin user already exists: {TENANT_ADMIN_EMAIL}")

        # Membership row — no role_id in the new schema.
        membership = (
            db.query(UserTenant)
            .filter(
                UserTenant.user_id == user.id,
                UserTenant.tenant_id == tenant.id,
            )
            .first()
        )
        if membership is None:
            db.add(
                UserTenant(
                    user_id=user.id,
                    tenant_id=tenant.id,
                )
            )
            print("[+] Membership created")
        else:
            print("[=] Membership already exists")

        # Role grant via the M2M user_roles table.
        existing_assignment = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user.id,
                UserRole.tenant_id == tenant.id,
                UserRole.role_id == admin_role.id,
            )
            .first()
        )
        if existing_assignment is None:
            db.add(
                UserRole(
                    user_id=user.id,
                    tenant_id=tenant.id,
                    role_id=admin_role.id,
                )
            )
            print(f"[+] Granted system role '{SYSTEM_ADMIN_ROLE_NAME}' to tenant admin")
        else:
            print(f"[=] Tenant admin already holds system role '{SYSTEM_ADMIN_ROLE_NAME}'")

        db.commit()

        print()
        print("Tenant seeding completed successfully")
        print(f"  Tenant Name:        {TENANT_NAME}")
        print(f"  Tenant Admin Email: {TENANT_ADMIN_EMAIL}")

    except Exception:
        db.rollback()
        print("Seed FAILED — all changes rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
