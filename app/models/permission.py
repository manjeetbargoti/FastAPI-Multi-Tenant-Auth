import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixinx import TimestampMixin
from app.models.role_permission import RolePermission

class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7()
    )

    # Permissions are GLOBAL across the platform: one row per code, shared by all tenants.
    code: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    # Logical grouping label (e.g. "user", "role", "tenant"); useful for UI grouping & filtering.
    category: Mapped[str | None] = mapped_column(String(50), index=True)

    # "tenant" / "platform" — capability surface this permission targets.
    scope: Mapped[str] = mapped_column(String(20), default="tenant")

    roles = relationship(
        "Role",
        secondary=RolePermission.__table__,
        back_populates="permissions",
        lazy="joined",
    )
