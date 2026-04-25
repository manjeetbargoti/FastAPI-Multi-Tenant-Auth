from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.permission import PermissionOutput


class RoleInfo(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permission_ids: List[UUID] = []


class RoleOutPut(BaseModel):
    id: UUID
    # NULL for system roles, a tenant UUID for tenant-owned roles.
    tenant_id: UUID | None = None
    name: str
    description: str | None = None
    is_system: bool = False

    class Config:
        from_attributes = True


class RoleDetail(BaseModel):
    """A role plus the full list of permissions it grants."""

    id: UUID
    tenant_id: UUID | None = None
    name: str
    description: str | None = None
    is_system: bool = False
    permissions: List[PermissionOutput] = []

    class Config:
        from_attributes = True


class RolePermissionUpdate(BaseModel):
    """Replace the entire permission set of a role with this exact list."""

    permission_ids: List[UUID]
