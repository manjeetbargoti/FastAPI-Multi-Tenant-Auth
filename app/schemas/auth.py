from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import List, Optional
from app.schemas.tenant import TenantInfo

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# class TenantInfo(BaseModel):
#     tenant_id: UUID
#     role_id: Optional[UUID]

class TokenResponse(BaseModel):
    user_id: UUID
    is_super_admin: bool
    tenants: List[TenantInfo]
    access_token: str
    token_type: str = "bearer"
    expires_in_min: int

class TenantRegistrationRequest(BaseModel):
    tenant_name: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class TenantRegistrationResponse(BaseModel):
    tenant_id: UUID
    user_id: UUID
    message: str

