from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.role import (
    RoleCreate,
    RoleOutPut,
    RoleDetail,
    RolePermissionUpdate,
)
from app.dependencies.auth import get_tenant_context
from app.dependencies.permissions import require_permission
from app.core.config.database import get_db
from app.services.role_service import RoleService

tenant_role_router = APIRouter(tags=["Tenant Roles"], prefix="/roles")


# ---- create / list ------------------------------------------------------

@tenant_role_router.post(
    "/create",
    response_model=RoleOutPut,
    dependencies=[Depends(require_permission("role.create"))],
)
def create_role(
    data: RoleCreate,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    try:
        role = RoleService(db).create_role(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            permission_ids=data.permission_ids,
        )

        db.commit()
        return role

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@tenant_role_router.get(
    "/list",
    response_model=list[RoleOutPut],
    dependencies=[Depends(require_permission("role.list"))],
)
def role_list(
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    try:
        return RoleService(db).list_roles_by_tenant(tenant_id=tenant_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ---- detail -------------------------------------------------------------

@tenant_role_router.get(
    "/{role_id}",
    response_model=RoleDetail,
    dependencies=[Depends(require_permission("role.list"))],
)
def role_detail(
    role_id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    try:
        return RoleService(db).get_role_in_tenant(
            role_id=role_id, tenant_id=tenant_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


# ---- permission-set management -----------------------------------------
#
# Note: all three endpoints below operate on TENANT-OWNED roles only.
# System roles (admin/member/viewer) are shared across every tenant and
# are blocked at the service layer with a 403.

@tenant_role_router.put(
    "/{role_id}/permissions",
    response_model=RoleDetail,
    dependencies=[Depends(require_permission("role.update"))],
)
def replace_role_permissions(
    role_id: UUID,
    data: RolePermissionUpdate,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    """Replace the role's entire permission set with the given list."""
    try:
        role = RoleService(db).set_permissions(
            role_id=role_id,
            tenant_id=tenant_id,
            permission_ids=data.permission_ids,
        )
        db.commit()
        return role
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@tenant_role_router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model=RoleDetail,
    dependencies=[Depends(require_permission("role.update"))],
)
def add_role_permission(
    role_id: UUID,
    permission_id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    """Idempotently grant a single permission to the role."""
    try:
        role = RoleService(db).add_permission(
            role_id=role_id,
            tenant_id=tenant_id,
            permission_id=permission_id,
        )
        db.commit()
        return role
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@tenant_role_router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("role.update"))],
)
def remove_role_permission(
    role_id: UUID,
    permission_id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    """Idempotently revoke a single permission from the role."""
    try:
        RoleService(db).remove_permission(
            role_id=role_id,
            tenant_id=tenant_id,
            permission_id=permission_id,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
