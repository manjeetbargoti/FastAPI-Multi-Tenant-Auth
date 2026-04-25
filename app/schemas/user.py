from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    password: str
    # Multiple roles per (user, tenant) are allowed; an empty list means
    # "membership only, no roles" (caller can grant later).
    role_ids: List[UUID] = []


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
    id: UUID
    name: str

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: UUID
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    is_active: bool
    is_verified: bool
    roles: List[UserRoleInfo] = []
