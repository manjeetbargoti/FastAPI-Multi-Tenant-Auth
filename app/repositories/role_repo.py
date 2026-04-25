from uuid import UUID

from sqlalchemy import or_

from app.repositories.base_repo import BaseRepository
from app.models.role import Role


class RoleRepo(BaseRepository):
    def create(
        self,
        name: str,
        tenant_id: UUID | None = None,
        description: str | None = None,
        is_system: bool = False,
        scope: str = "tenant",
    ) -> Role:
        role = Role(
            name=name,
            tenant_id=tenant_id,
            description=description,
            is_system=is_system,
            scope=scope,
        )
        self.db.add(instance=role)
        self.db.flush()
        return role

    def get_by_id(self, role_id: UUID) -> Role | None:
        """Unscoped lookup by id. Returns the role regardless of tenant or system status."""
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_by_id_in_tenant(self, role_id: UUID, tenant_id: UUID) -> Role | None:
        """
        Lookup a role that is usable inside `tenant_id`.

        Matches either a tenant-owned role (Role.tenant_id == tenant_id) or a
        system role (Role.tenant_id IS NULL).
        """
        return (
            self.db.query(Role)
            .filter(
                Role.id == role_id,
                or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
            )
            .first()
        )

    def get_by_name(self, name: str, tenant_id: UUID) -> Role | None:
        """Tenant-scoped lookup by name. Does NOT match system roles."""
        return (
            self.db.query(Role)
            .filter(Role.tenant_id == tenant_id, Role.name == name)
            .first()
        )

    def get_system_role(self, name: str) -> Role | None:
        return (
            self.db.query(Role)
            .filter(Role.tenant_id.is_(None), Role.name == name)
            .first()
        )

    def list_for_tenant(self, tenant_id: UUID) -> list[Role]:
        """Every role available within a tenant: tenant-owned + system."""
        return (
            self.db.query(Role)
            .filter(or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)))
            .order_by(Role.is_system.desc(), Role.name.asc())
            .all()
        )

    def list_system_roles(self) -> list[Role]:
        return (
            self.db.query(Role)
            .filter(Role.tenant_id.is_(None))
            .order_by(Role.name.asc())
            .all()
        )
