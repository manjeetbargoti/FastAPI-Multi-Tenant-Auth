from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.schemas.role import RoleInfo


class PlatformTenantCreate(BaseModel):
    tenant_name: str
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None


class PlatformTenantOut(BaseModel):
    tenant_id: UUID
    user_id: UUID
    message: str

    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    name: str


class TenantOut(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class TenantInfo(BaseModel):
    tenant_id: UUID
    # Every role the user holds within this tenant. May be empty for a
    # member who has no role grants yet.
    roles: List[RoleInfo] = []

    class Config:
        from_attributes = True
