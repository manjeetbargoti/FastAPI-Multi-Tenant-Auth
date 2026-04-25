"""
Declarative catalog of the platform's SYSTEM roles.

System roles are seeded once with `tenant_id IS NULL` and `is_system=True`.
They are visible to every tenant and cannot be modified through tenant-scoped
endpoints (see `RoleService._get_modifiable_role`).

This catalog is the source of truth for `app/cli/system_seed.py`. Editing
this file and re-running the seed will reconcile both the role set AND each
role's permission set in the database.
"""

from typing import TypedDict


class SystemRoleSpec(TypedDict):
    name: str
    description: str
    # When True, the role is granted EVERY code in TENANT_PERMISSIONS at
    # seed time. When False, only the explicit `permissions` list is granted.
    grant_all: bool
    permissions: list[str]


SYSTEM_ROLES: list[SystemRoleSpec] = [
    {
        "name": "admin",
        "description": "Full administrative access within a tenant.",
        "grant_all": True,
        "permissions": [],
    },
    {
        "name": "member",
        "description": "Regular tenant member with basic read access.",
        "grant_all": False,
        "permissions": [
            "tenant.read",
        ],
    },
    {
        "name": "viewer",
        "description": "Read-only access across users, roles and tenant data.",
        "grant_all": False,
        "permissions": [
            "tenant.read",
            "user.list",
            "role.list",
        ],
    },
]
