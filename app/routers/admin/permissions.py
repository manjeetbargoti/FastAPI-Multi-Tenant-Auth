from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.dependencies.auth import get_current_user, get_tenant_context
from app.models.user import User
from app.services.permission_service import PermissionService

perm_router = APIRouter(tags=["Platfrom Permission"], prefix="/platform/permissions")

@perm_router.post("/sync", status_code=status.HTTP_200_OK)
def sync_permissions_for_tenant(tenant_id = Depends(get_tenant_context), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # Platform admin only
        if not current_user.is_super_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only platform admin can sync permissions")
        
        PermissionService(db=db).sync_permissions_for_tenant(tenant_id=tenant_id)
        db.commit()

        return {
            "message": "Permissions synced successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    