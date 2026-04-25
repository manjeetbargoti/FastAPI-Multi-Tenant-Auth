from pydantic import BaseModel
from typing import List
from uuid import UUID

class RoleInfo(BaseModel):
    id: UUID | None
    name: str | None
    
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    permission_ids: List[UUID] = []

class RoleOutPut(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str

    class Config:
        from_attributes = True
        