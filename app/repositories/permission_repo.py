from uuid import UUID

from app.repositories.base_repo import BaseRepository
from app.models.permission import Permission


class PermissionRepo(BaseRepository):
    """Permissions are GLOBAL — never scoped by tenant."""

    def create(
        self,
        code: str,
        description: str | None = None,
        category: str | None = None,
        scope: str = "tenant",
    ) -> Permission:
        permission = Permission(
            code=code,
            description=description,
            category=category,
            scope=scope,
        )
        self.db.add(instance=permission)
        self.db.flush()
        return permission

    def get_by_id(self, permission_id: UUID) -> Permission | None:
        return self.db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_code(self, code: str) -> Permission | None:
        return self.db.query(Permission).filter(Permission.code == code).first()

    def list_all(self) -> list[Permission]:
        return self.db.query(Permission).order_by(Permission.code.asc()).all()
