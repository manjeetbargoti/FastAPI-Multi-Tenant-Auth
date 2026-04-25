from app.repositories.base_repo import BaseRepository
from app.models.user import User
from app.models.user_tenant import UserTenant
from uuid import UUID
from sqlalchemy.orm import joinedload

class UserRepo(BaseRepository):

    def add(self, user: User) -> User:
        self.db.add(instance=user)
        self.db.flush()
        return user
    
    def get_by_email(self, email: str) -> User | None:
        return (
            self.db.query(User).filter(User.email == email).first()
        )
    
    def get_by_id(self, user_id: UUID) -> User | None:
        return (
            self.db.query(User).filter(User.id == user_id).first()
        )
    
    def get_user_tenants(self, user_id: UUID) -> list[UserTenant]:
        """
        Return all tenant memberships for a global user.
        """
        return (
            self.db.query(UserTenant).options(joinedload(UserTenant.role)).filter(UserTenant.user_id == user_id).all()
        )
    
    def exists_by_email(self, email: str) -> bool:
        return (
            self.db.query(User).filter(User.email == email).first() 
            is not None
        )
    
    def is_member_of_tenant(self, user_id: UUID, tenant_id: UUID) -> bool:
        return (
            self.db.query(UserTenant).filter(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            ).first() 
            is not None
        )
    
    def get_user_by_tenant(self, tenant_id: UUID) -> list[User]:
        """
        Return all users belonging to a tenant.
        """
        users = (
            self.db.query(UserTenant).options(joinedload(UserTenant.user),joinedload(UserTenant.role)).filter(
                UserTenant.tenant_id == tenant_id
            ).all()
        )

        return users
