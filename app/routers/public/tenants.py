from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.schemas.auth import TenantRegistrationRequest, TenantRegistrationResponse
from app.services.tenant_service import TenantRegistrationService

tenant_router = APIRouter(tags=["Public Tenant"], prefix="/public/tenant")

@tenant_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TenantRegistrationResponse)
def register_tenant(data: TenantRegistrationRequest, db: Session = Depends(get_db)):
    try:
        tenant, user = TenantRegistrationService(db).register_tenant(
            tenant_name = data.tenant_name,
            email = data.email.lower(),
            password = data.password,
            first_name = data.first_name,
            last_name = data.last_name
        )

        db.commit()

        return TenantRegistrationResponse(
            tenant_id=tenant.id,
            user_id=user.id,
            message="Tenant registered successfully."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
