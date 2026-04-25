from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.permission_repo import PermissionRepo
from app.repositories.role_repo import RoleRepo
from app.models.tenant import Tenant
from app.core.permissions.definitions import TENANT_PERMISSIONS


class PermissionService:
    def __init__(self, db: Session):
        self.db = db
        self.permission_repo = PermissionRepo(db)
        self.role_repo = RoleRepo(db)

    def sync_permissions_for_tenant(self, tenant_id: UUID) -> None:
        # 1️. Ensure admin role exists
        admin_role = self.role_repo.get_by_name(name="admin", tenant_id=tenant_id)
        if not admin_role:
            admin_role = self.role_repo.create(tenant_id=tenant_id, name="admin")

        # 2️. Fetch existing permissions
        existing_permissions = {
            p.code: p for p in self.permission_repo.list_by_tenant(tenant_id)
        }

        # 3️. Create missing permissions
        for code, description in TENANT_PERMISSIONS:
            if code not in existing_permissions:
                permission = self.permission_repo.create(
                    tenant_id=tenant_id,
                    code=code,
                    description=description,
                )
                existing_permissions[code] = permission

        # 4️. Ensure admin role has ALL permissions
        for permission in existing_permissions.values():
            if permission not in admin_role.permissions:
                admin_role.permissions.append(permission)


    def permission_list_by_tenant(self, tenant_id: UUID) -> list[Tenant]:
        permissions = self.permission_repo.list_by_tenant(tenant_id=tenant_id)

        return permissions
    