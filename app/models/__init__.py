from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.user_tenant import UserTenant

# Re-exported so SQLAlchemy's declarative registry sees every mapped class
# whenever `app.models` is imported (e.g. by Alembic env.py).
__all__ = [
    "Tenant",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "UserTenant",
]
