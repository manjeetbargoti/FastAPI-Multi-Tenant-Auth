from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config.database import get_db
from app.core.security.security import decode_token
from app.models.user import User
from app.models.user_tenant import UserTenant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

#++++++++++++++++++#
# Get current user #
#++++++++++++++++++#
def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(
        User.id == UUID(user_id),
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    return user


#++++++++++++++++++++#
# Get current tenant #
#++++++++++++++++++++#
def get_tenant_context(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UUID:
    """
    Resolve and validate tenant for this request.

    Tenant must be provided vis `X-Tenant-ID` header.
    """
    tenant_id = request.headers.get("X-Tenant-ID")

    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Tenant-ID header is required")
    
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant id format")
    
    # Super Admin bypasses tenant id check
    if user.is_super_admin:
        return tenant_uuid
    
    tenant_link = db.query(UserTenant).filter_by(user_id=user.id, tenant_id=tenant_uuid).first()

    if not tenant_link:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not belong to this tenant")
    
    return tenant_uuid
