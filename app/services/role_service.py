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
        self.permission_repo = PermissionRepo(db=db)

    def create_role(
        self,
        tenant_id: UUID,
        name: str,
        description: str | None = None,
        permission_ids: list[UUID] | None = None,
    ) -> Role:
        """
        Create a tenant-owned role. Always `is_system=False` — system roles
        are seeded once at the platform level.

        Caller is responsible for committing the surrounding transaction.
        """
        if self.role_repo.get_by_name(name=name, tenant_id=tenant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{name}' already exists in this tenant.",
            )

        # Tenant-owned role gets blocked from accidental "admin"-style name
        # collisions with system roles via the role_repo.get_by_name lookup
        # above — note that lookup ONLY matches tenant_id == this tenant, so
        # tenants CAN create a custom role that shadows a system role name.
        # We accept that intentionally: tenant policy may legitimately want a
        # custom "admin" with different permissions.
        role = self.role_repo.create(
            name=name,
            tenant_id=tenant_id,
            description=description,
            is_system=False,
        )

        if permission_ids:
            permissions = []
            for perm_id in permission_ids:
                permission = self.permission_repo.get_by_id(permission_id=perm_id)
                if not permission:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Permission with ID '{perm_id}' not found.",
                    )
                permissions.append(permission)

            role.permissions.extend(permissions)

        return role

    def list_roles_by_tenant(self, tenant_id: UUID) -> list[Role]:
        """
        Roles available within a tenant: tenant-owned roles + every system
        role (admin/member/viewer/...).
        """
        return self.role_repo.list_for_tenant(tenant_id=tenant_id)

    # ---- detail / lookup -----------------------------------------------

    def get_role_in_tenant(self, role_id: UUID, tenant_id: UUID) -> Role:
        """
        Resolve a role usable inside `tenant_id` (tenant-owned OR system).
        Raises 404 if not found, so callers don't leak information about
        roles belonging to other tenants.
        """
        role = self.role_repo.get_by_id_in_tenant(
            role_id=role_id, tenant_id=tenant_id
        )
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found in this tenant",
            )
        return role

    # ---- permission-set management -------------------------------------

    def set_permissions(
        self,
        role_id: UUID,
        tenant_id: UUID,
        permission_ids: list[UUID],
    ) -> Role:
        """
        Replace a role's entire permission set with `permission_ids`.

        Caller is responsible for committing the surrounding transaction.
        """
        role = self._get_modifiable_role(role_id=role_id, tenant_id=tenant_id)

        new_perms = []
        for pid in permission_ids:
            permission = self.permission_repo.get_by_id(permission_id=pid)
            if permission is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permission with ID '{pid}' not found.",
                )
            new_perms.append(permission)

        role.permissions = new_perms
        self.db.flush()
        return role

    def add_permission(
        self,
        role_id: UUID,
        tenant_id: UUID,
        permission_id: UUID,
    ) -> Role:
        """Idempotently grant a single permission to a role."""
        role = self._get_modifiable_role(role_id=role_id, tenant_id=tenant_id)

        permission = self.permission_repo.get_by_id(permission_id=permission_id)
        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found.",
            )

        if permission not in role.permissions:
            role.permissions.append(permission)
            self.db.flush()

        return role

    def remove_permission(
        self,
        role_id: UUID,
        tenant_id: UUID,
        permission_id: UUID,
    ) -> None:
        """Idempotently revoke a single permission from a role."""
        role = self._get_modifiable_role(role_id=role_id, tenant_id=tenant_id)

        permission = self.permission_repo.get_by_id(permission_id=permission_id)
        if permission is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found.",
            )

        if permission in role.permissions:
            role.permissions.remove(permission)
            self.db.flush()

    # ---- internal -------------------------------------------------------

    def _get_modifiable_role(self, role_id: UUID, tenant_id: UUID) -> Role:
        """
        Return a role this tenant is allowed to MUTATE.

        System roles (is_system=True) are shared globally across every tenant
        and are intentionally NOT writable through tenant-scoped endpoints —
        any modification would silently affect every other tenant. Block here.
        """
        role = self.get_role_in_tenant(role_id=role_id, tenant_id=tenant_id)
        if role.is_system:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System roles cannot be modified by tenants.",
            )
        return role
