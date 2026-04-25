import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixinx import TimestampMixin

class UserRole(Base, TimestampMixin):
    """
    Real M2M assignment of a Role to a User within a specific Tenant.

    A single (user, tenant) pair may carry MULTIPLE roles; uniqueness is on the
    full triple (user_id, tenant_id, role_id).
    """
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", "role_id", name="uq_user_tenant_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7()
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Audit: who granted this role assignment. Nullable so deleting the granter
    # doesn't wipe the assignment itself.
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user = relationship(
        "User",
        back_populates="user_roles",
        foreign_keys=[user_id],
    )
    tenant = relationship("Tenant", back_populates="role_assignments")
    role = relationship("Role", back_populates="user_assignments")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
