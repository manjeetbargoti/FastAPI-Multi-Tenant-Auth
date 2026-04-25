import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixinx import TimestampMixin

class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7()
    )
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    users = relationship("UserTenant", back_populates="tenant", cascade="all, delete-orphan")
    # Tenant-owned (non-system) roles. System roles live with tenant_id IS NULL
    # and are NOT included in this collection.
    roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")
    role_assignments = relationship("UserRole", back_populates="tenant", cascade="all, delete-orphan")
