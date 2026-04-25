from pydantic import BaseModel, EmailStr
from uuid import UUID
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
    role: RoleInfo

    class Config:
        from_attributes = True
        