from uuid import UUID

from sqlalchemy.orm import joinedload

from app.repositories.base_repo import BaseRepository
from app.models.user_role import UserRole


class UserRoleRepo(BaseRepository):
    """CRUD for the (user, tenant, role) M2M assignment."""

    def create(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role_id: UUID,
        granted_by: UUID | None = None,
    ) -> UserRole:
        assignment = UserRole(
            user_id=user_id,
            tenant_id=tenant_id,
            role_id=role_id,
            granted_by=granted_by,
        )
        self.db.add(instance=assignment)
        self.db.flush()
        return assignment

    def exists(self, user_id: UUID, tenant_id: UUID, role_id: UUID) -> bool:
        return (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
                UserRole.role_id == role_id,
            )
            .first()
            is not None
        )

    def list_for_user(self, user_id: UUID) -> list[UserRole]:
        """Every assignment a user has, across all tenants. Eager-loads Role."""
        return (
            self.db.query(UserRole)
            .options(joinedload(UserRole.role))
            .filter(UserRole.user_id == user_id)
            .all()
        )

    def list_for_user_in_tenant(self, user_id: UUID, tenant_id: UUID) -> list[UserRole]:
        return (
            self.db.query(UserRole)
            .options(joinedload(UserRole.role))
            .filter(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
            )
            .all()
        )

    def list_for_tenant(self, tenant_id: UUID) -> list[UserRole]:
        """Every role assignment inside a tenant, with Role eager-loaded."""
        return (
            self.db.query(UserRole)
            .options(joinedload(UserRole.role))
            .filter(UserRole.tenant_id == tenant_id)
            .all()
        )

    def delete(self, user_id: UUID, tenant_id: UUID, role_id: UUID) -> bool:
        deleted = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
                UserRole.role_id == role_id,
            )
            .delete(synchronize_session=False)
        )
        return deleted > 0
