"""
Platform-level RBAC bootstrap.

Idempotently:
  1. Inserts every code in `TENANT_PERMISSIONS` into the global `permissions` table.
  2. Creates the system roles defined in `SYSTEM_ROLES` (tenant_id=NULL, is_system=True).
  3. Reconciles each system role's permission set to match the catalog.

Run AFTER `alembic upgrade head` and BEFORE any tenant registration.
Re-running is safe and will repair any drift in system-role permission sets.

    python app/cli/system_seed.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from sqlalchemy.orm import Session

from app.core.config.database import SessionLocal
from app.core.permissions.definitions import TENANT_PERMISSIONS
from app.core.permissions.system_roles import SYSTEM_ROLES
from app.models.permission import Permission
from app.repositories.permission_repo import PermissionRepo
from app.repositories.role_repo import RoleRepo
from app.services.permission_service import PermissionService


def _sync_system_roles(
    db: Session,
    all_permissions: list[Permission],
) -> tuple[int, int]:
    """
    Create missing system roles and reconcile every system role's permission
    set against the catalog. Returns (created_count, updated_count).
    """
    role_repo = RoleRepo(db=db)
    code_to_perm = {p.code: p for p in all_permissions}

    # `admin`'s "grant_all" is resolved against the canonical definitions list,
    # NOT against the DB. This keeps the seed deterministic even if extra
    # permission rows linger in the DB from prior catalogs.
    canonical_codes = [code for code, _ in TENANT_PERMISSIONS]

    created = 0
    updated = 0

    for spec in SYSTEM_ROLES:
        name = spec["name"]
        description = spec["description"]
        wanted_codes = (
            canonical_codes if spec["grant_all"] else list(spec["permissions"])
        )

        # Resolve every requested code BEFORE writing — fail loudly on a typo
        # in `system_roles.py` rather than silently shipping an underpowered role.
        wanted_perms: list[Permission] = []
        for code in wanted_codes:
            permission = code_to_perm.get(code)
            if permission is None:
                raise RuntimeError(
                    f"System role '{name}' references unknown permission "
                    f"code '{code}'. Add it to TENANT_PERMISSIONS in "
                    f"app/core/permissions/definitions.py or remove it from "
                    f"SYSTEM_ROLES in app/core/permissions/system_roles.py."
                )
            wanted_perms.append(permission)

        role = role_repo.get_system_role(name=name)
        if role is None:
            role = role_repo.create(
                name=name,
                tenant_id=None,
                description=description,
                is_system=True,
            )
            created += 1
            print(f"[+] Created system role: {name}")

        # Reconcile description (cheap idempotent overwrite).
        if role.description != description:
            role.description = description

        # Reconcile permission set. SQLAlchemy diffs the collection and emits
        # only the necessary INSERT/DELETE on role_permissions.
        current_codes = {p.code for p in role.permissions}
        wanted_code_set = {p.code for p in wanted_perms}
        if current_codes != wanted_code_set:
            role.permissions = wanted_perms
            updated += 1
            removed = current_codes - wanted_code_set
            added = wanted_code_set - current_codes
            print(
                f"[~] Updated permissions for system role '{name}': "
                f"+{len(added)} -{len(removed)}"
            )
        else:
            print(f"[=] System role '{name}' already in sync ({len(wanted_perms)} perms)")

    return created, updated


def run():
    db = SessionLocal()

    try:
        # 1. Sync the global permission catalog.
        created_perms = PermissionService(db=db).sync_permissions_global()
        if created_perms:
            print(f"[+] Created {created_perms} new permission(s)")
        else:
            print("[=] Permission catalog already in sync")

        # Re-fetch from DB so freshly inserted rows are included for role linking.
        all_perms = PermissionRepo(db=db).list_all()

        # 2. Sync system roles + their permission sets.
        created_roles, updated_roles = _sync_system_roles(
            db=db, all_permissions=all_perms
        )

        db.commit()

        print()
        print("System seed complete")
        print(f"  Permissions in catalog: {len(all_perms)}")
        print(f"  System roles created:   {created_roles}")
        print(f"  System roles updated:   {updated_roles}")

    except Exception:
        db.rollback()
        print("System seed FAILED — all changes rolled back.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
