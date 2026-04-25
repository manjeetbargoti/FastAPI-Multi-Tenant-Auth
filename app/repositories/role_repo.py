from uuid import UUID
from app.repositories.base_repo import BaseRepository
from app.models.role import Role

class RoleRepo(BaseRepository):

    def create(self, tenant_id: UUID, name: str) -> Role:
        role = Role(tenant_id=tenant_id, name=name)
        self.db.add(instance=role)
        self.db.flush()
        return role
    
    def get_by_id(self, role_id: UUID, tenant_id: UUID) -> Role | None:
        return (
            self.db.query(Role).filter(Role.tenant_id == tenant_id, Role.id == role_id).first()
        )
    
    def get_by_name(self, name: str, tenant_id: UUID) -> Role | None:
        return (
            self.db.query(Role).filter(Role.tenant_id == tenant_id, Role.name == name).first()
        )
    
    def list_by_tenant(self, tenant_id: UUID) -> list[Role]:
        return (
            self.db.query(Role).filter(Role.tenant_id == tenant_id).all()
        )
    