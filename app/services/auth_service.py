from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.user_repo import UserRepo
from app.core.security.security import verify_password, create_access_token

from app.models.user import User
from app.models.user_tenant import UserTenant
from app.core.config.settings import Settings

settings = Settings()

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepo(db=db)

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a global user and return:
        - global access token (no tenant bound)
        - list of tenants the user belongs to
        """
        user: User | None = self.user_repo.get_by_email(email=email)

        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        
        # Global token - no tenant in token
        token = create_access_token(
            {
                "sub": str(user.id),
                "is_super_admin": user.is_super_admin
            }
        )

        # Fetch linked tenants
        tenants: list[UserTenant] = self.user_repo.get_user_tenants(user_id=user.id)

        return {
            "user_id": str(user.id),
            "is_super_admin": user.is_super_admin,
            "tenants": [
                {
                    "tenant_id": str(t.tenant_id),
                    "role": {
                        "id": str(t.role.id) if t.role.id else None,
                        "name": str(t.role.name) if t.role.name else None
                    }
                }
                for t in tenants
            ],
            "access_token": token,
            "token_type": "bearer", 
            "expires_in_min": settings.ACCESS_TOKEN_EXPIRE_MINUTES
        }
        