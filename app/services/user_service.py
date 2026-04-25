from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.repositories.user_repo import UserRepo
from app.repositories.user_tenant_repo import UserTenantRepo
from app.repositories.user_role_repo import UserRoleRepo
from app.repositories.role_repo import RoleRepo
from app.core.security.security import hash_password
from app.schemas.user import UserListItem, UserRoleInfo


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepo(db=db)
        self.user_tenant_repo = UserTenantRepo(db=db)
        self.user_role_repo = UserRoleRepo(db=db)
        self.role_repo = RoleRepo(db=db)

    def create_user_in_tenant(
        self,
        tenant_id: UUID,
        email: str,
        password: str,
        first_name: str | None,
        last_name: str | None,
        role_ids: list[UUID] | None = None,
        invited_by: UUID | None = None,
        granted_by: UUID | None = None,
    ) -> User:
        """
        Get-or-create a global User, attach them to a tenant via UserTenant,
        and grant any number of roles (tenant-owned OR system) via UserRole.

        Caller is responsible for committing the surrounding transaction.
        """
        try:
            user = self.user_repo.get_by_email(email=email)

            if not user:
                user = User(
                    email=email,
                    password=hash_password(password),
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_verified=True,
                )
                self.user_repo.add(user=user)

            if self.user_tenant_repo.exists(user_id=user.id, tenant_id=tenant_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already exists in this tenant",
                )

            # Resolve every requested role against (tenant-owned OR system)
            # BEFORE writing anything else, so a bad role id aborts the whole op.
            resolved_roles = []
            for role_id in role_ids or []:
                role = self.role_repo.get_by_id_in_tenant(
                    role_id=role_id, tenant_id=tenant_id
                )
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid role '{role_id}' for this tenant",
                    )
                resolved_roles.append(role)

            self.user_tenant_repo.create(
                user_id=user.id,
                tenant_id=tenant_id,
                invited_by=invited_by,
            )

            for role in resolved_roles:
                self.user_role_repo.create(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    role_id=role.id,
                    granted_by=granted_by,
                )

            return user

        except HTTPException:
            raise
        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user in tenant",
            )

    def list_users_in_tenant(self, tenant_id: UUID) -> list[UserListItem]:
        """
        Active members of a tenant, each with the FULL list of roles they
        hold inside that tenant.
        """
        memberships = self.user_repo.get_user_by_tenant(tenant_id=tenant_id)
        assignments = self.user_role_repo.list_for_tenant(tenant_id=tenant_id)

        # Group roles by user_id once; O(N) instead of N+1 per-user lookups.
        roles_by_user: dict[UUID, list[UserRoleInfo]] = {}
        for ur in assignments:
            roles_by_user.setdefault(ur.user_id, []).append(
                UserRoleInfo(id=ur.role.id, name=ur.role.name)
            )

        result: list[UserListItem] = []
        for m in memberships:
            u = m.user
            result.append(
                UserListItem(
                    id=u.id,
                    email=u.email,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    is_active=u.is_active,
                    is_verified=u.is_verified,
                    roles=roles_by_user.get(u.id, []),
                )
            )

        return result

    # ---- role assignment management ------------------------------------

    def assign_role(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
        granted_by: UUID | None = None,
    ) -> UserRole:
        """
        Grant a role to a user inside a tenant.

        - Target user must already be a member of the tenant.
        - Role must be tenant-owned OR a system role.
        - Idempotent: re-assigning an existing (user, tenant, role) returns
          the existing assignment instead of erroring.

        Caller is responsible for committing the surrounding transaction.
        """
        if not self.user_tenant_repo.exists(user_id=user_id, tenant_id=tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this tenant",
            )

        role = self.role_repo.get_by_id_in_tenant(
            role_id=role_id, tenant_id=tenant_id
        )
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found in this tenant",
            )

        if self.user_role_repo.exists(
            user_id=user_id, tenant_id=tenant_id, role_id=role_id
        ):
            existing = next(
                (
                    ur
                    for ur in self.user_role_repo.list_for_user_in_tenant(
                        user_id=user_id, tenant_id=tenant_id
                    )
                    if ur.role_id == role_id
                ),
                None,
            )
            # `existing` cannot be None here because exists() returned True;
            # the assert keeps type-checkers honest.
            assert existing is not None
            return existing

        return self.user_role_repo.create(
            user_id=user_id,
            tenant_id=tenant_id,
            role_id=role_id,
            granted_by=granted_by,
        )

    def revoke_role(
        self,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
    ) -> None:
        """
        Remove a single (user, tenant, role) assignment.

        Strict: 404 if the user is not in the tenant OR the assignment
        doesn't exist. Caller commits.
        """
        if not self.user_tenant_repo.exists(user_id=user_id, tenant_id=tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this tenant",
            )

        deleted = self.user_role_repo.delete(
            user_id=user_id, tenant_id=tenant_id, role_id=role_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role assignment not found",
            )

    def list_user_roles_in_tenant(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> list[Role]:
        """Every role this user holds inside `tenant_id`."""
        if not self.user_tenant_repo.exists(user_id=user_id, tenant_id=tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this tenant",
            )

        assignments = self.user_role_repo.list_for_user_in_tenant(
            user_id=user_id, tenant_id=tenant_id
        )
        return [ur.role for ur in assignments]
