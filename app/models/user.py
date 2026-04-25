import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixinx import TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7()
    )

    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    tenants = relationship(
        "UserTenant",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserTenant.user_id",
    )
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserRole.user_id",
    )

    def roles_by_tenant(self, tenant_id: uuid.UUID) -> list["Role"]:
        """
        Return every Role this user holds within the given tenant.

        Operates on the already-loaded `user_roles` collection; eager-load it
        (e.g. via selectinload) at the call site if you want to avoid lazy I/O.
        """
        return [ur.role for ur in self.user_roles if ur.tenant_id == tenant_id]
