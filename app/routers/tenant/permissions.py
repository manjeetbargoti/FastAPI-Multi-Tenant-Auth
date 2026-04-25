from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.dependencies.auth import get_tenant_context
from app.services.permission_service import PermissionService
from app.schemas.permission import PermissionOutput

tenant_perm_router = APIRouter(tags=["Tenant Permission"], prefix="/permissions")


@tenant_perm_router.get("/permission-list", response_model=list[PermissionOutput])
def permission_list(
    # Tenant context kept as a dependency: ensures only authenticated users
    # with an active membership can browse the (global) permission catalog.
    tenant_id=Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    try:
        return PermissionService(db=db).list_permissions()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
