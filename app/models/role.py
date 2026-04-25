import uuid
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixinx import TimestampMixin
from app.models.role_permission import RolePermission

class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    __table_args__ = (
        # Tenant-specific roles: name unique within a tenant.
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
        # System roles (tenant_id IS NULL): name must be globally unique.
        # Postgres treats NULLs as distinct in regular unique constraints, so we use
        # a partial unique index to enforce uniqueness across system roles.
        Index(
            "uq_role_system_name",
            "name",
            unique=True,
            postgresql_where=text("tenant_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7()
    )

    # NULL == system role (available to all tenants); non-NULL == tenant-owned role.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    # Built-in roles (admin/member/viewer) carry is_system=True and must not be deletable.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # "tenant" / "platform"
    scope: Mapped[str] = mapped_column(String(20), default="tenant")

    tenant = relationship("Tenant", back_populates="roles")
    permissions = relationship(
        "Permission",
        secondary=RolePermission.__table__,
        back_populates="roles",
        lazy="joined",
    )
    user_assignments = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )
