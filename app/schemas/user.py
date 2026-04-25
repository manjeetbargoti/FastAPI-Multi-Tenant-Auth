from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    password: str
    role_id: UUID | None = None

class UserOutput(BaseModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    is_active: bool
    is_verified: bool
    
    class Config: 
        from_attributes = True

class UserRoleInfo(BaseModel):
    id: UUID | None
    name: str | None

class UserListItem(BaseModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    is_active: bool
    is_verified: bool
    role: UserRoleInfo

        