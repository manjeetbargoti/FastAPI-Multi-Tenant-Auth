import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from app.core.config.database import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.user_tenant import UserTenant
from app.core.security.security import hash_password
from app.services.permission_service import PermissionService

TENANT_NAME = "default"
TENANT_ADMIN_EMAIL = "admin@tenant.com"
TENANT_ADMIN_PASSOWRD = "Tenant@123"

def run():
    db = SessionLocal()

    try:
        # 1. Create tenant if not exists
        tenant = db.query(Tenant).filter(Tenant.name == TENANT_NAME).first()
        if not tenant:
            tenant = Tenant(name=TENANT_NAME)
            db.add(tenant)
            db.flush()

            db.commit()
            print("Tenant created: ", TENANT_NAME)
        else:
            print("Tenant already exists: ", TENANT_NAME)

        # 2. Create tenant admin user if not exists
        user = db.query(User).filter(User.email == TENANT_ADMIN_EMAIL).first()
        if not user:
            user = User(
                email=TENANT_ADMIN_EMAIL,
                password=hash_password(TENANT_ADMIN_PASSOWRD),
                first_name="Tenant",
                last_name="Admin",
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.flush()

            print("Tenant admin user created: ", TENANT_ADMIN_EMAIL)
        else:
            print("Tenant admin user already exists: ", TENANT_ADMIN_EMAIL)

        # 3. Create tenant admin role if not exists
        admin_role = db.query(Role).filter(Role.name == "admin", Role.tenant_id == tenant.id).first()

        if not admin_role:
            admin_role = Role(
                name="admin",
                tenant_id=tenant.id,
                scope="tenant"
            )
            db.add(admin_role)
            db.flush()

            print("Tenant admin role created")
        else:
            print("Tenant admin role already exists")

        # 4. Sync permissions for tenant
        PermissionService(db).sync_permissions_for_tenant(tenant.id)
        print("Permissions synced for tenant")

        # 5. Assign tenant admin role to tenant admin user
        user_tenant = db.query(UserTenant).filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == tenant.id
        ).first()

        if not user_tenant:
            user_tenant = UserTenant(
                user_id=user.id,
                tenant_id=tenant.id,
                role_id=admin_role.id
            )
            db.add(user_tenant)

            print("Assigned admin role to tenant admin user")
        else:
            print("Tenant admin user already has admin role assigned")

        db.commit()

        print("\n Tenant seeding completed successfully")
        print("Tenant Name:", TENANT_NAME)
        print("Tenant Admin Email:", TENANT_ADMIN_EMAIL)
        print("Tenant Admin Password:", TENANT_ADMIN_PASSOWRD)

    except Exception as e:
        db.rollback()
        print("Seed failed:")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run()

