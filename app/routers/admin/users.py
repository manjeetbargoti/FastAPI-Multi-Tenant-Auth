from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.dependencies.auth import get_current_user, get_tenant_context
from app.dependencies.permissions import require_permission
from app.models.user import User
from app.schemas.user import UserCreate, UserOutput, UserListItem
from app.schemas.role import RoleInfo
from app.services.user_service import UserService

user_router = APIRouter(tags=["Users"], prefix="/users")


# ---- create / list ------------------------------------------------------

@user_router.post(
    "/create",
    response_model=UserOutput,
    dependencies=[Depends(require_permission("user.create"))],
)
def create_user(
    data: UserCreate,
    tenant_id: UUID = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a global user (or attach an existing one) to the current tenant
    and grant any number of roles via `role_ids`."""
    try:
        user = UserService(db).create_user_in_tenant(
            tenant_id=tenant_id,
            email=data.email.lower(),
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            role_ids=data.role_ids,
            invited_by=current_user.id,
            granted_by=current_user.id,
        )

        db.commit()
        return user

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@user_router.get(
    "/list",
    response_model=list[UserListItem],
    dependencies=[Depends(require_permission("user.list"))],
)
def list_users(
    tenant_id: UUID = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).list_users_in_tenant(tenant_id=tenant_id)


# ---- role-assignment endpoints -----------------------------------------
#
# IMPORTANT: `/users/me/roles` MUST be declared BEFORE `/users/{user_id}/roles`
# so FastAPI matches the literal `me` segment first; otherwise it would be
# captured by the dynamic {user_id} parameter and fail UUID validation.

@user_router.get(
    "/me/roles",
    response_model=list[RoleInfo],
)
def list_my_roles(
    tenant_id: UUID = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List the authenticated user's own roles inside the current tenant.

    No specific permission required: any active member can read their own
    role grants. Membership is already enforced by `get_tenant_context`.
    """
    try:
        return UserService(db).list_user_roles_in_tenant(
            tenant_id=tenant_id, user_id=current_user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@user_router.get(
    "/{user_id}/roles",
    response_model=list[RoleInfo],
    dependencies=[Depends(require_permission("user.list"))],
)
def list_user_roles(
    user_id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    """List every role assigned to `user_id` inside the current tenant."""
    try:
        return UserService(db).list_user_roles_in_tenant(
            tenant_id=tenant_id, user_id=user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@user_router.post(
    "/{user_id}/roles/{role_id}",
    response_model=RoleInfo,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("user.update"))],
)
def assign_role_to_user(
    user_id: UUID,
    role_id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Grant `role_id` to `user_id` inside the current tenant.

    - 404 if the user isn't a member of this tenant.
    - 404 if the role isn't tenant-owned or system.
    - Idempotent: re-grants return 201 with the same role payload.
    """
    try:
        assignment = UserService(db).assign_role(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
            granted_by=current_user.id,
        )
        db.commit()
        return assignment.role

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@user_router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("user.update"))],
)
def revoke_role_from_user(
    user_id: UUID,
    role_id: UUID,
    tenant_id: UUID = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    """
    Remove a single (user, tenant, role) assignment.

    Strict: 404 if the assignment doesn't exist (no silent success).
    """
    try:
        UserService(db).revoke_role(
            tenant_id=tenant_id,
            user_id=user_id,
            role_id=role_id,
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
