from pydantic import BaseModel
from uuid import UUID

class PermissionOutput(BaseModel):
    id: UUID
    code: str
    description: str | None = None

    class Config:
        from_attributes = True
        