from app.repositories.base_repo import BaseRepository
from app.models.user_tenant import UserTenant
from uuid import UUID

class UserTenantRepo(BaseRepository):
    def exists(self, user_id: UUID, tenant_id: UUID) -> bool:
        return (
            self.db.query(UserTenant).filter(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            ).first() is not None
        )
    
    def create(self, user_id: UUID, tenant_id: UUID, role_id: UUID):
        user_tenant = UserTenant(user_id=user_id, tenant_id=tenant_id, role_id=role_id)
        self.db.add(instance=user_tenant)
        self.db.flush()
        return user_tenant
    