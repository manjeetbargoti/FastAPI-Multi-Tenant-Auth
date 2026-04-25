from uuid import UUID
from app.repositories.base_repo import BaseRepository
from app.models.permission import Permission

class PermissionRepo(BaseRepository):
    def create(self, tenant_id: UUID, code: str, description: str | None = None) -> Permission:
        permission = Permission(
            tenant_id=tenant_id,
            code=code,
            description=description,
            scope="tenant"
        )
        self.db.add(instance=permission)
        self.db.flush()
        return permission
    
    def get_by_id(self, permission_id: UUID, tenant_id: UUID) -> Permission | None:
        return (
            self.db.query(Permission).filter(Permission.tenant_id == tenant_id, Permission.id == permission_id).first()
        )
    
    def get_by_code(self, tenant_id: UUID, code: str) -> Permission | None:
        return (
            self.db.query(Permission).filter(
                Permission.tenant_id == tenant_id,
                Permission.code == code
            ).first()
        )
    
    def list_by_tenant(self, tenant_id: UUID) -> list[Permission]:
        return (
            self.db.query(Permission).filter(Permission.tenant_id == tenant_id).order_by(Permission.code.asc()).all()
        )