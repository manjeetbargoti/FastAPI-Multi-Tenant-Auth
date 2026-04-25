from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config.database import get_db
from app.dependencies.auth import get_current_user, get_tenant_context
from app.models.user import User
from app.models.user_tenant import UserTenant

def require_permission(code: str):
    def checker(
            tenant_id: UUID = Depends(get_tenant_context),
            user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
    ):
        #  Super Admin bypass
        if user.is_super_admin:
            return
        
        tenant_link = (
            db.query(UserTenant).filter(
                UserTenant.user_id == user.id,
                UserTenant.tenant_id == tenant_id
            ).first()
        )

        if not tenant_link or not tenant_link.role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No role assign in this tenant")
        
        # Check permission via Role -> Permission
        if not any(p.code == code for p in tenant_link.role.permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {code}")
    
    return checker
