from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.role import RoleCreate, RoleOutPut
from app.dependencies.auth import get_tenant_context
from app.dependencies.permissions import require_permission
from app.core.config.database import get_db
from app.services.role_service import RoleService

role_router = APIRouter(tags=["Roles"], prefix="/roles")

@role_router.post("/create", response_model=RoleOutPut, dependencies=[Depends(require_permission("role.create"))])
def create_role(data: RoleCreate, tenant_id=Depends(get_tenant_context), db: Session = Depends(get_db)):
    try:
        role = RoleService(db).create_role(
            tenant_id=tenant_id,
            name=data.name,
            permission_ids=data.permission_ids
        )

        db.commit()
        
        return role
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
