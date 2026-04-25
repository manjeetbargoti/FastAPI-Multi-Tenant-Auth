from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.permission_service import PermissionService

perm_router = APIRouter(tags=["Platform Permission"], prefix="/platform/permissions")


@perm_router.post("/sync", status_code=status.HTTP_200_OK)
def sync_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Idempotently insert any permission listed in `TENANT_PERMISSIONS` that
    is missing from the database.

    Permissions are GLOBAL — there is no tenant scope. This endpoint is the
    one place to refresh the platform permission catalog after editing
    `app/core/permissions/definitions.py`.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform admin can sync permissions",
        )

    try:
        created_count = PermissionService(db=db).sync_permissions_global()
        db.commit()

        return {
            "message": "Permissions synced successfully",
            "created": created_count,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
