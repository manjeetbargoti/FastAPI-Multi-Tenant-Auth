# FastAPI Multi-Tenant Auth

A production-oriented FastAPI backend implementing **multi-tenancy**, **JWT authentication**, and **role-based access control (RBAC)**. Each tenant has its own isolated set of roles and permissions, with a global platform super-admin that can manage all tenants.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Database Models](#database-models)
- [Authentication & Authorization Flow](#authentication--authorization-flow)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Setup](#database-setup)
  - [Bootstrap (Optional)](#bootstrap-optional)
  - [Running the Server](#running-the-server)
- [Permission System](#permission-system)
- [Known Caveats](#known-caveats)

---

## Features

- **Multi-tenancy** — Users belong to multiple tenants simultaneously; each membership carries its own role.
- **JWT Authentication** — Stateless tokens issued at login; tenant context selected per-request via header.
- **Role-Based Access Control (RBAC)** — Per-tenant roles with granular permission codes; permissions are auto-synced from a canonical catalog.
- **Platform Super Admin** — A global super-admin flag on users that bypasses tenant membership and permission checks.
- **Public Tenant Self-Registration** — Unauthenticated endpoint for creating a new tenant and an initial admin user.
- **Layered Architecture** — Clean separation: router → service → repository → SQLAlchemy ORM.
- **Alembic Migrations** — Full migration history with autogenerate support.
- **CLI Bootstrap Scripts** — One-command seeding for platform admin and default tenant.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **FastAPI** | Web framework, OpenAPI/Swagger generation |
| **Uvicorn** | ASGI server |
| **SQLAlchemy 2.x** | ORM and query builder |
| **PostgreSQL** | Primary database (UUID PKs, FK cascade rules) |
| **psycopg2-binary** | PostgreSQL driver |
| **Alembic** | Database schema migrations |
| **Pydantic v2 / pydantic-settings** | Request/response validation, environment config |
| **python-jose[cryptography]** | JWT encode/decode |
| **passlib[argon2]** | Argon2 password hashing |
| **python-multipart** | Form/multipart support |

---

## Project Structure

```
.
├── main.py                          # App factory; mounts /api/v1 router
├── alembic.ini                      # Alembic configuration
├── requirements.txt                 # Python dependencies
├── .env                             # Local environment variables (do not commit)
│
├── alembic/
│   ├── env.py                       # Migration runtime; imports ORM metadata
│   ├── script.py.mako               # Migration file template
│   └── versions/
│       └── 456d7a345c4b_init_multi_tenant_rbac.py  # Initial RBAC schema migration
│
└── app/
    ├── core/
    │   ├── config/
    │   │   ├── settings.py          # Pydantic BaseSettings (reads from .env)
    │   │   └── database.py          # Engine, SessionLocal, get_db() dependency
    │   ├── security/
    │   │   └── security.py          # Argon2 hashing, JWT create/decode
    │   └── permissions/
    │       └── definitions.py       # Canonical TENANT_PERMISSIONS catalog
    │
    ├── dependencies/
    │   ├── auth.py                  # get_current_user, get_tenant_context (X-Tenant-ID)
    │   └── permissions.py           # require_permission(code) dependency factory
    │
    ├── models/
    │   ├── user.py                  # User, UserTenant
    │   ├── tenant.py                # Tenant
    │   ├── role.py                  # Role, RolePermission
    │   ├── permission.py            # Permission
    │   └── mixinx.py               # TimestampMixin (created_at, updated_at, deleted_at)
    │
    ├── schemas/
    │   ├── auth.py                  # LoginRequest, TokenResponse
    │   ├── user.py                  # UserCreate, UserOutput, UserListItem
    │   ├── tenant.py                # Tenant create/register DTOs
    │   ├── role.py                  # RoleCreate, RoleOutPut, RoleInfo
    │   └── permission.py            # PermissionOutput
    │
    ├── repositories/
    │   ├── base.py                  # BaseRepository (holds Session)
    │   ├── user_repo.py             # UserRepo (with joinedload for memberships)
    │   ├── tenant_repo.py           # TenantRepo
    │   ├── role_repo.py             # RoleRepo
    │   └── permission_repo.py       # PermissionRepo
    │
    ├── services/
    │   ├── auth_service.py          # Login, token validation
    │   ├── user_service.py          # User creation, listing
    │   ├── tenant_service.py        # Tenant creation, permission sync
    │   ├── role_service.py          # Role CRUD, role assignment
    │   └── permission_service.py    # sync_permissions_for_tenant
    │
    ├── routers/
    │   ├── routes_v1.py             # Aggregates all v1 routers
    │   ├── admin/
    │   │   ├── auth.py              # POST /auth/login
    │   │   ├── users.py             # POST /users/create, GET /users/list
    │   │   ├── roles.py             # POST /roles/create
    │   │   ├── tenants.py           # POST /platform/tenant/create (super admin)
    │   │   └── permissions.py       # POST /platform/permissions/sync (not wired)
    │   ├── tenant/
    │   │   ├── roles.py             # POST /roles/create, GET /roles/list
    │   │   └── permissions.py       # GET /permissions/permission-list
    │   └── public/
    │       └── tenants.py           # POST /public/tenant/register (no auth)
    │
    ├── cli/
    │   ├── platform_user.py         # Create platform super-admin
    │   └── tenant_seed.py           # Seed default tenant + admin
    │
    └── utils/
        └── permission_marker.py     # @permission(code) decorator stub
```

---

## Architecture Overview

The application follows a strict **four-layer architecture**:

```
HTTP Request
    │
    ▼
Router (FastAPI APIRouter)
    │  validates input schema, enforces auth/permission via Depends()
    ▼
Service (business logic)
    │  orchestrates rules, calls multiple repositories
    ▼
Repository (data access)
    │  encapsulates SQLAlchemy queries
    ▼
SQLAlchemy ORM / PostgreSQL
```

**Key dependency chain for protected endpoints:**

```
Depends(get_current_user)           ← decodes JWT, loads User
Depends(get_tenant_context)         ← reads X-Tenant-ID header, validates membership
Depends(require_permission("code")) ← checks role.permissions for the tenant
```

---

## Database Models

### `users`
Global user identity. One user can be a member of many tenants.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `email` | String | Unique |
| `password` | String | Argon2 hash |
| `is_active` | Boolean | Default `True` |
| `is_verified` | Boolean | Default `False` |
| `is_super_admin` | Boolean | Default `False`; bypasses all tenant checks |
| `verified_at` | DateTime | Nullable |
| `created_at`, `updated_at`, `deleted_at` | DateTime | Via `TimestampMixin` |

### `tenants`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | String | Unique |
| `is_active` | Boolean | Default `True` |
| `created_at`, `updated_at` | DateTime | |

### `user_tenants` (membership)

Links a user to a tenant with an optional role. The **primary RBAC join** used by the app.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → `users` | |
| `tenant_id` | UUID FK → `tenants` | |
| `role_id` | UUID FK → `roles` | Nullable; one role per membership |
| Unique | `(user_id, tenant_id)` | |

### `roles`

Per-tenant roles with a many-to-many relationship to permissions.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `name` | String | Unique per tenant |
| `tenant_id` | UUID FK → `tenants` | |
| `scope` | String | Default `"tenant"` |

### `permissions`

Per-tenant permission codes synced from the canonical catalog.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `code` | String | Unique per tenant (e.g. `user.create`) |
| `description` | String | Human-readable label |
| `tenant_id` | UUID FK → `tenants` | |
| `scope` | String | |

### `role_permissions`
Association table between `roles` and `permissions`.

---

## Authentication & Authorization Flow

### 1. Login
```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secret
```
Returns a **global JWT** containing `sub` (user UUID) and `is_super_admin`. The token is **not** bound to a specific tenant.

### 2. Authenticated Request
Send the token and the desired tenant for every protected request:
```
GET /api/v1/users/list
Authorization: Bearer <token>
X-Tenant-ID: <tenant-uuid>
```

### 3. Authorization checks (in order)
1. **`get_current_user`** — decodes JWT, loads `User` from DB, checks `is_active`.
2. **`get_tenant_context`** — validates `X-Tenant-ID`; requires a `UserTenant` row for non-super-admins.
3. **`require_permission("code")`** — checks that the user's role for that tenant includes the required permission code. Super admins are always allowed.

### Password security
- Argon2 hashing via `passlib`.
- Passwords are capped at 72 UTF-8 bytes before hashing.

---

## API Endpoints

All routes are mounted under `/api/v1`.

| Method | Path | Auth | Notes |
|---|---|---|---|
| `GET` | `/` | None | Root health check |
| `GET` | `/health` | None | Health check |
| `POST` | `/auth/login` | None | Returns JWT token |
| `POST` | `/public/tenant/register` | None | Self-service tenant + admin creation |
| `POST` | `/platform/tenant/create` | Super admin | Create tenant (admin only) |
| `POST` | `/users/create` | JWT + Tenant + `user.create` | Create user in tenant |
| `GET` | `/users/list` | JWT + Tenant + `user.list` | List users in tenant |
| `POST` | `/roles/create` | JWT + Tenant | Create role in tenant |
| `GET` | `/roles/list` | JWT + Tenant | List roles in tenant |
| `GET` | `/permissions/permission-list` | JWT + Tenant | List permissions in tenant |

> **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) and [http://localhost:8000/redoc](http://localhost:8000/redoc).

---

## Environment Variables

Create a `.env` file in the project root. All keys are **case-sensitive**.

```env
# Application
APP_NAME=FastAPI Multi-Tenant Auth
DEBUG=True
FRONTEND_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT
JWT_SECRET_KEY=your-very-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EMAIL_TOKEN_EXPIRE_MINUTES=1440

# Mail (required by Settings even if not actively used)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@example.com
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- `pip` or a virtual-environment manager of your choice

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd fast-api-multi-tenant-auth

# Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env   # or create .env manually (see section above)
```

### Database Setup

```bash
# Apply all migrations
alembic upgrade head
```

> Make sure `DATABASE_URL` in `.env` and `sqlalchemy.url` in `alembic.ini` point to the same database, or export `DATABASE_URL` before running Alembic.

### Bootstrap (Optional)

These scripts create initial users with hardcoded credentials. **Change credentials before use in any shared environment.**

```bash
# Create a platform super-admin (admin@platform.com)
python app/cli/platform_user.py

# Seed a default tenant and a tenant admin (admin@tenant.com)
python app/cli/tenant_seed.py
```

### Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## Permission System

Permissions are defined in `app/core/permissions/definitions.py` as a list of `(code, description)` tuples (e.g. `user.create`, `user.list`, `role.create`).

When a new tenant is created (via either public registration or admin endpoint), `PermissionService.sync_permissions_for_tenant` automatically:

1. Creates any missing `Permission` rows for that tenant from the catalog.
2. Ensures the built-in **`admin`** role for that tenant has all permissions assigned.

This means adding a new permission to `definitions.py` and re-running the sync will propagate it to all tenants without manual DB edits.

To check a permission in a route:

```python
from app.dependencies.permissions import require_permission

@router.get("/my-resource")
def list_resources(
    _: None = Depends(require_permission("resource.list")),
    db: Session = Depends(get_db),
):
    ...
```

---

## Known Caveats

| Issue | Location | Detail |
|---|---|---|
| **Unreachable sync endpoint** | `app/routers/admin/permissions.py` | `perm_router` is defined but not included in `routes_v1.py`; the `/platform/permissions/sync` route cannot be reached via HTTP. |
| **Duplicate route prefixes** | `app/routers/admin/roles.py` vs `app/routers/tenant/roles.py` | Both use `/roles/create`; consolidate prefixes to avoid conflicts in OpenAPI and routing. |
| **`UserRole` table unused** | `app/models/`, migrations | The `user_roles` association table exists in the schema but the application resolves roles through `UserTenant.role_id`, not `UserRole`. |
| **`list_users_in_tenant` indentation bug** | `app/services/user_service.py` | The result-building loop may only retain the last user due to a mis-indented `result` assignment; verify and fix before relying on list endpoints in production. |
| **Mail settings required** | `app/core/config/settings.py` | All `MAIL_*` variables must be present in `.env` even though `fastapi_mail` is not currently wired into any router or service. Make them optional (`Optional[str] = None`) to remove this requirement. |
