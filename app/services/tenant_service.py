from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.tenant_repo import TenantRepo
from app.repositories.user_repo import UserRepo
from app.repositories.user_tenant_repo import UserTenantRepo
from app.repositories.user_role_repo import UserRoleRepo
from app.repositories.role_repo import RoleRepo
from app.models.user import User
from app.core.security.security import hash_password


# Name of the global system role granted to the user that registers a new
# tenant (or that a platform admin attaches to a freshly created tenant).
# Must exist in the DB before this service runs — seeded by app/cli/.
DEFAULT_OWNER_SYSTEM_ROLE = "admin"


class TenantRegistrationService:
    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepo(db)
        self.user_repo = UserRepo(db)
        self.user_tenant_repo = UserTenantRepo(db)
        self.user_role_repo = UserRoleRepo(db)
        self.role_repo = RoleRepo(db)

    # ---- public ---------------------------------------------------------

    def register_tenant(
        self,
        tenant_name: str,
        email: str,
        password: str,
        first_name: str | None,
        last_name: str | None,
    ):
        """Self-service tenant signup. The signing-up user becomes the owner."""
        return self._provision_tenant(
            tenant_name=tenant_name,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            invited_by=None,
            granted_by=None,
        )

    def create_tenant_by_platform(
        self,
        tenant_name: str,
        email: str,
        password: str,
        first_name: str | None,
        last_name: str | None,
        platform_admin_id=None,
    ):
        """Platform-admin-driven tenant creation. The platform admin is recorded as inviter/grantor."""
        return self._provision_tenant(
            tenant_name=tenant_name,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            invited_by=platform_admin_id,
            granted_by=platform_admin_id,
        )

    # ---- internal -------------------------------------------------------

    def _provision_tenant(
        self,
        tenant_name: str,
        email: str,
        password: str,
        first_name: str | None,
        last_name: str | None,
        invited_by,
        granted_by,
    ):
        """
        Single shared flow for both public and platform-driven tenant creation.

        Caller is responsible for committing the surrounding transaction.
        """
        if self.tenant_repo.get_by_name(name=tenant_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant with this name already exists.",
            )

        existing_user = self.user_repo.get_by_email(email=email)
        if existing_user is None and self.user_repo.exists_by_email(email=email):
            # Defensive: exists_by_email returning True with get_by_email returning None
            # would only happen on a race condition — surface a clear error rather
            # than silently overwriting.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists.",
            )

        # System "admin" role MUST exist (seeded once at platform setup).
        # We resolve it BEFORE creating any rows so the entire transaction
        # aborts cleanly if seeding hasn't run.
        admin_role = self.role_repo.get_system_role(name=DEFAULT_OWNER_SYSTEM_ROLE)
        if admin_role is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"System role '{DEFAULT_OWNER_SYSTEM_ROLE}' is not seeded. "
                    "Run the platform seed before registering tenants."
                ),
            )

        tenant = self.tenant_repo.create(name=tenant_name)

        if existing_user is not None:
            user = existing_user
        else:
            user = User(
                email=email,
                password=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=True,
            )
            self.user_repo.add(user=user)

        self.user_tenant_repo.create(
            user_id=user.id,
            tenant_id=tenant.id,
            invited_by=invited_by,
        )

        self.user_role_repo.create(
            user_id=user.id,
            tenant_id=tenant.id,
            role_id=admin_role.id,
            granted_by=granted_by,
        )

        return tenant, user
