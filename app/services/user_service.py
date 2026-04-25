from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_tenant import UserTenant
from app.models.role import Role
from app.repositories.user_repo import UserRepo
from app.core.security.security import hash_password
from app.schemas.user import UserListItem, UserRoleInfo

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepo(db=db)

    def create_user_in_tenant(self, tenant_id: UUID, email: str, password: str, first_name: str | None, last_name: str | None, role_id: UUID | None = None) -> User:
        """
        Create a global user (if not exists) and attach it to a tenant
        """
        try:
            # 1. Get or Create a Global User
            user = self.user_repo.get_by_email(email=email)

            if not user:
                user = User(
                    email=email,
                    password=hash_password(password),
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    is_verified=True
                )

                self.db.add(user)
                self.db.flush()

            # 2. Ensure user is not already in this tenant
            exists = (
                self.db.query(UserTenant).filter(
                    UserTenant.user_id == user.id,
                    UserTenant.tenant_id == tenant_id
                ).first()
            )

            if exists:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists in this tenant")
            
            # 3. Validate role (if provided)
            if role_id:
                role = (
                    self.db.query(Role).filter(
                        Role.id == role_id, Role.tenant_id == tenant_id
                    ).first()
                )

                if not role:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role for this tenant")
            
            # 4. Link User to Tenant
            tenant_link = UserTenant(
                user_id=user.id,
                tenant_id=tenant_id,
                role_id=role_id
            )

            self.db.add(tenant_link)
            self.db.flush()

            return user
        
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user in tenant")

    # List all users in tenant
    def list_users_in_tenant(self, tenant_id: UUID) -> list[User]:
        users = self.user_repo.get_user_by_tenant(tenant_id=tenant_id)

        result: list[UserListItem] = []

        for u in users:
            user = u.user
            role = u.role

        result.append(
            UserListItem(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                role=UserRoleInfo(
                    id=role.id if role else None,
                    name=role.name if role else None,
                )
            )
        )

        return result
    