import uuid
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.models.base import Base
from app.models.mixinx import TimestampMixin
from app.models.user_role import UserRole

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)     # 'True' for active, 'False' for not active
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)   # 'True' for verified, 'False' for not verified
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)      # 'True' for super-admin, 'False' for not super-admin

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    tenants = relationship("UserTenant", back_populates="user", cascade="all, delete-orphan")
