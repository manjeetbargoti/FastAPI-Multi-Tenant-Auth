from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.tenant_repo import TenantRepo
from app.repositories.user_repo import UserRepo
from app.repositories.user_tenant_repo import UserTenantRepo
from app.repositories.role_repo import RoleRepo
from app.models.user import User
from app.core.security.security import hash_password
from app.services.permission_service import PermissionService

class TenantRegistrationService:
    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepo(db)
        self.user_repo = UserRepo(db)
        self.user_tenant_repo = UserTenantRepo(db)
        self.role_repo = RoleRepo(db)

    def register_tenant(self, tenant_name: str, email: str, password: str, first_name: str | None, last_name: str | None):
        # 1. Guards
        if self.tenant_repo.get_by_name(name=tenant_name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant with this name already exists.")
        
        if self.user_repo.exists_by_email(email=email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
        
        try:
            # 2. Create Tenant
            tenant = self.tenant_repo.create(name=tenant_name)

            # 3. Get or Create User
            user = self.user_repo.get_by_email(email=email)

            if not user:
                user = User(
                    email=email,
                    password=hash_password(password),
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_verified=True
                )

                self.user_repo.add(user=user)

            # 4. Create Admin Role
            admin_role = self.role_repo.create(name="admin", tenant_id=tenant.id)

            # 5. Assign All Permissions to Admin Role
            PermissionService(db=self.db).sync_permissions_for_tenant(tenant_id=tenant.id)

            # 6. Assign User to Tenant with Admin Role
            self.user_tenant_repo.create(user_id=user.id, tenant_id=tenant.id, role_id=admin_role.id)

            return tenant, user
        
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    def create_tenant_by_platform(self, tenant_name: str, email: str, password: str, first_name: str | None, last_name: str | None):
        # 1. Guards
        if self.tenant_repo.get_by_name(name=tenant_name):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant with this name already exists.")
        
        if self.user_repo.exists_by_email(email=email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
        
        try:
            # 2. Create Tenant
            tenant = self.tenant_repo.create(name=tenant_name)

            # 3. Get or Create User
            user = self.user_repo.get_by_email(email=email)

            if not user:
                user = User(
                    email=email,
                    password=hash_password(password),
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_verified=True
                )

                user = self.user_repo.add(user=user)

            # 4. Create Admin Role
            admin_role = self.role_repo.create(name="admin", tenant_id=tenant.id)

            # 5. Assign All Permissions to Admin Role
            PermissionService(db=self.db).sync_permissions_for_tenant(tenant_id=tenant.id)

            # 6. Assign User to Tenant with Admin Role
            self.user_tenant_repo.create(user_id=user.id, tenant_id=tenant.id, role_id=admin_role.id)

            return tenant, user
        
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        