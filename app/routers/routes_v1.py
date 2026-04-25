from fastapi import APIRouter

from app.routers.admin.auth import auth_router
from app.routers.admin.tenants import admin_tenant_router
from app.routers.admin.users import user_router
from app.routers.admin.permissions import perm_router as admin_perm_router
from app.routers.public.tenants import tenant_router as public_tenant_router
from app.routers.tenant.permissions import tenant_perm_router
from app.routers.tenant.roles import tenant_role_router

routes_v1 = APIRouter()

# Auth
routes_v1.include_router(router=auth_router)

# Platform-admin routes
routes_v1.include_router(router=admin_tenant_router)
routes_v1.include_router(router=admin_perm_router)

# Tenant-scoped routes (require X-Tenant-ID header)
routes_v1.include_router(router=user_router)
routes_v1.include_router(router=tenant_perm_router)
routes_v1.include_router(router=tenant_role_router)

# Public (unauthenticated) routes
routes_v1.include_router(router=public_tenant_router)
