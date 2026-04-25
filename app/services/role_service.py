from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.role_repo import RoleRepo
from app.repositories.permission_repo import PermissionRepo

class RoleService:
    def __init__(self, db: Session):
        self.db = db
        self.role_repo = RoleRepo(db=db)
        self.permissions = PermissionRepo(db=db)

    def create_role(self, tenant_id: UUID, name: str, permission_ids: list[UUID] | None = None) -> Role:
        try:
            # 1. Prevent duplicate role names within the same tenant
            if self.role_repo.get_by_name(name=name, tenant_id=tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with name '{name}' already exists."
                )

            # 2. Create Role
            role = self.role_repo.create(tenant_id=tenant_id, name=name)

            # 3. Assign Permissions if provided
            if permission_ids:
                permissions = []
                for perm_id in permission_ids:
                    permission = self.permissions.get_by_id(permission_id=perm_id, tenant_id=tenant_id)
                    if not permission:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Permission with ID '{perm_id}' not found."
                        )
                    permissions.append(permission)
                
                role.permissions.extend(permissions)

            return role
            
        except Exception as e:
            self.db.rollback()
            raise e
        
    def list_roles_by_tenant(self, tenant_id: UUID) -> list[Role]:
        try:
            return self.role_repo.list_by_tenant(tenant_id=tenant_id)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        