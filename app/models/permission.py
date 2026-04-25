import uuid
from sqlalchemy import String, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixinx import TimestampMixin
from app.models.role_permission import RolePermission

class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_permission_tenant_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    code: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    scope: Mapped[str] = mapped_column(String(20), default="tenant")        # "tenant" / "platform"

    roles = relationship("Role", secondary=RolePermission.__table__, back_populates="permissions", lazy="joined")
