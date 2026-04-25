from uuid import UUID

from app.repositories.base_repo import BaseRepository
from app.models.user_tenant import UserTenant


class UserTenantRepo(BaseRepository):
    def exists(self, user_id: UUID, tenant_id: UUID) -> bool:
        return (
            self.db.query(UserTenant)
            .filter(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id,
            )
            .first()
            is not None
        )

    def get(self, user_id: UUID, tenant_id: UUID) -> UserTenant | None:
        return (
            self.db.query(UserTenant)
            .filter(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id,
            )
            .first()
        )

    def create(
        self,
        user_id: UUID,
        tenant_id: UUID,
        invited_by: UUID | None = None,
    ) -> UserTenant:
        membership = UserTenant(
            user_id=user_id,
            tenant_id=tenant_id,
            invited_by=invited_by,
        )
        self.db.add(instance=membership)
        self.db.flush()
        return membership

    def list_for_user(self, user_id: UUID, only_active: bool = True) -> list[UserTenant]:
        q = self.db.query(UserTenant).filter(UserTenant.user_id == user_id)
        if only_active:
            q = q.filter(UserTenant.is_active.is_(True))
        return q.all()

    def list_for_tenant(self, tenant_id: UUID, only_active: bool = True) -> list[UserTenant]:
        q = self.db.query(UserTenant).filter(UserTenant.tenant_id == tenant_id)
        if only_active:
            q = q.filter(UserTenant.is_active.is_(True))
        return q.all()
