from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepo
from app.repositories.user_role_repo import UserRoleRepo
from app.core.security.security import verify_password, create_access_token

from app.models.user import User
from app.core.config.settings import Settings

settings = Settings()


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepo(db=db)
        self.user_role_repo = UserRoleRepo(db=db)

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a global user and return:
          - a global access token (no tenant bound)
          - the list of tenants the user belongs to, each with EVERY role the
            user holds inside that tenant (multiple roles per tenant supported).
        """
        user: User | None = self.user_repo.get_by_email(email=email)

        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        token = create_access_token(
            {
                "sub": str(user.id),
                "is_super_admin": user.is_super_admin,
            }
        )

        # 1 query for active memberships, 1 query for ALL role assignments,
        # then we group in Python. Keeps it O(2) regardless of tenant count.
        memberships = self.user_repo.get_user_tenants(user_id=user.id, only_active=True)
        assignments = self.user_role_repo.list_for_user(user_id=user.id)

        roles_by_tenant: dict[UUID, list[dict]] = {}
        for ur in assignments:
            roles_by_tenant.setdefault(ur.tenant_id, []).append(
                {"id": str(ur.role.id), "name": ur.role.name}
            )

        return {
            "user_id": str(user.id),
            "is_super_admin": user.is_super_admin,
            "tenants": [
                {
                    "tenant_id": str(m.tenant_id),
                    "roles": roles_by_tenant.get(m.tenant_id, []),
                }
                for m in memberships
            ],
            "access_token": token,
            "token_type": "bearer",
            "expires_in_min": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        }
