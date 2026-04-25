from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.tenant import PlatformTenantCreate
from app.core.config.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.tenant_service import TenantRegistrationService

admin_tenant_router = APIRouter(tags=["Platform Tenant"], prefix="/platform/tenant")

@admin_tenant_router.post("/create", status_code=status.HTTP_201_CREATED)
def create_tenant_by_platform(data: PlatformTenantCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if not current_user.is_super_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can create tenants.")
        
        tenant, user = TenantRegistrationService(db=db).create_tenant_by_platform(
            tenant_name=data.tenant_name,
            email=data.email.lower(),
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name
        )

        db.commit()

        return {
            "tenant_id": tenant.id,
            "user_id": user.id,
            "message": "Tenant created successfully."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
