from sqlalchemy.orm import Session

from app.repositories.permission_repo import PermissionRepo
from app.models.permission import Permission
from app.core.permissions.definitions import TENANT_PERMISSIONS


class PermissionService:
    """
    Permissions are GLOBAL across the platform — there is exactly one row per
    `code` and that row is shared by every tenant. Sync is a platform-level
    operation, NOT a per-tenant one.
    """

    def __init__(self, db: Session):
        self.db = db
        self.permission_repo = PermissionRepo(db)

    def sync_permissions_global(self) -> int:
        """
        Idempotently insert any permission listed in TENANT_PERMISSIONS that
        does not yet exist. Returns the number of NEW rows created (existing
        rows are left untouched, including their `description`/`category`).

        Caller is responsible for committing the surrounding transaction.
        """
        existing = {p.code: p for p in self.permission_repo.list_all()}
        created_count = 0

        for code, description in TENANT_PERMISSIONS:
            if code in existing:
                continue

            category = code.split(".", 1)[0] if "." in code else None
            self.permission_repo.create(
                code=code,
                description=description,
                category=category,
                scope="tenant",
            )
            created_count += 1

        return created_count

    def list_permissions(self) -> list[Permission]:
        """All permissions defined on the platform, ordered by code."""
        return self.permission_repo.list_all()
