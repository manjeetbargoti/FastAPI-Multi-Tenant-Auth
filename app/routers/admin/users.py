from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.database import get_db
from app.dependencies.auth import get_current_user, get_tenant_context
from app.models.user import User
from app.schemas.user import UserCreate, UserOutput, UserListItem
from app.services.user_service import UserService
from app.dependencies.permissions import require_permission

user_router = APIRouter(tags=["Users"], prefix="/users")

@user_router.post("/create", response_model=UserOutput, dependencies=[Depends(require_permission("user.create"))])
def create_user(
    data: UserCreate,
    tenant_id: UUID = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Only tenant admins or super admins should be allowed here.
    If you have a permission system wired, enfore it here.
    """
    try:
        user = UserService(db).create_user_in_tenant(
            tenant_id=tenant_id,
            email=data.email.lower(),
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            role_id=data.role_id
        )

        db.commit()

        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@user_router.get("/list", response_model=list[UserListItem], dependencies=[Depends(require_permission("user.list"))])
def list_users(
    tenant_id: UUID = Depends(get_tenant_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = UserService(db).list_users_in_tenant(tenant_id=tenant_id)

    return users
