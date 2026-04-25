import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

class UserTenant(Base):
    """
    Pure membership row linking a User to a Tenant.

    Role assignments live in the `user_roles` table, NOT here. A user can be
    deactivated from a tenant via `is_active = False` (soft removal).
    """
    __tablename__ = "user_tenants"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Audit: who invited this user into the tenant. Null for self-registered owners.
    invited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Soft-removal flag: False == user no longer participates in this tenant.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    user = relationship(
        "User",
        back_populates="tenants",
        foreign_keys=[user_id],
    )
    tenant = relationship("Tenant", back_populates="users")
    invited_by_user = relationship("User", foreign_keys=[invited_by])
