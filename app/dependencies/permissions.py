from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.dependencies.auth import get_current_user, get_tenant_context
from app.models.user import User
from app.models.user_tenant import UserTenant
from app.models.user_role import UserRole
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.permission import Permission


def require_permission(code: str):
    """
    FastAPI dependency factory: blocks the request unless the caller's roles
    inside the resolved tenant collectively grant `code`.

    Resolution path:
      1. Super-admins bypass (no DB read).
      2. Caller must hold an ACTIVE UserTenant membership for this tenant.
      3. Caller must hold at least one Role (tenant-owned OR system) inside
         this tenant whose RolePermission set includes `code`.

    The permission check is a single JOIN — no N+1 over roles.
    """

    def checker(
        tenant_id: UUID = Depends(get_tenant_context),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        if user.is_super_admin:
            return

        # Active membership is mandatory; soft-removed users are blocked here.
        active_member = (
            db.query(UserTenant.id)
            .filter(
                UserTenant.user_id == user.id,
                UserTenant.tenant_id == tenant_id,
                UserTenant.is_active.is_(True),
            )
            .first()
        )
        if not active_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active membership in this tenant",
            )

        # Single query: does ANY role this user holds in this tenant grant `code`?
        # UserRole -> Role -> RolePermission -> Permission
        has_perm = (
            db.query(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(
                UserRole.user_id == user.id,
                UserRole.tenant_id == tenant_id,
                Permission.code == code,
            )
            .first()
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {code}",
            )

    return checker
