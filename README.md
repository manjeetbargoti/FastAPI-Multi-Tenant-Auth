# FastAPI Multi-Tenant Auth

A production-oriented FastAPI backend implementing **multi-tenancy**, **JWT authentication**, and **role-based access control (RBAC)**. Users can belong to multiple tenants simultaneously, each membership carrying its own set of roles. Permissions are global and shared across the platform; roles are either system-wide (seeded once) or tenant-owned (created per tenant).

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Database Models](#database-models)
- [Authentication & Authorization Flow](#authentication--authorization-flow)
- [Permission System](#permission-system)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Setup](#database-setup)
  - [Bootstrap — required order](#bootstrap--required-order)
  - [Running the Server](#running-the-server)
- [Known Caveats](#known-caveats)

---

## Features

- **Multi-tenancy** — One user can belong to many tenants; each membership is an independent row with its own role grants.
- **JWT Authentication** — Stateless tokens issued at login; tenant context supplied per-request via `X-Tenant-ID` header.
- **Role-Based Access Control (RBAC)** — Roles carry granular permission codes. A user may hold multiple roles inside a tenant (true M2M). Permissions are global (not per-tenant).
- **System Roles** — `admin`, `member`, `viewer` seeded once at platform level (`tenant_id IS NULL`), visible to every tenant, immutable via tenant-scoped API.
- **Platform Super Admin** — A `is_super_admin` flag on users that bypasses all tenant membership and permission checks.
- **Public Tenant Self-Registration** — Unauthenticated endpoint for creating a new tenant and an initial owner user.
- **Layered Architecture** — Router → Service → Repository → SQLAlchemy ORM.
- **Alembic Migrations** — Single clean init migration; autogenerate-ready.
- **CLI Bootstrap Scripts** — Three idempotent scripts that must run in order after a fresh migration.

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
│       └── 531cc8a977ae_init_multi_tenant_rbac.py  # Clean init migration
│
└── app/
    ├── core/
    │   ├── config/
    │   │   ├── settings.py          # Pydantic BaseSettings (reads from .env)
    │   │   └── database.py          # Engine, SessionLocal, get_db() dependency
    │   ├── security/
    │   │   └── security.py          # Argon2 hashing, JWT create/decode
    │   └── permissions/
    │       ├── definitions.py       # TENANT_PERMISSIONS catalog — source of truth
    │       └── system_roles.py      # SYSTEM_ROLES declarative catalog
    │
    ├── dependencies/
    │   ├── auth.py                  # get_current_user, get_tenant_context (X-Tenant-ID)
    │   └── permissions.py           # require_permission(code) dependency factory
    │
    ├── models/
    │   ├── base.py                  # Declarative base (re-export from database.py)
    │   ├── mixinx.py                # TimestampMixin (created_at, updated_at, deleted_at)
    │   ├── tenant.py                # Tenant
    │   ├── user.py                  # User
    │   ├── permission.py            # Permission (global, no tenant_id)
    │   ├── role.py                  # Role (tenant_id nullable → system roles)
    │   ├── role_permission.py       # RolePermission (M2M join table)
    │   ├── user_role.py             # UserRole (M2M, surrogate PK, tenant_id, granted_by)
    │   └── user_tenant.py           # UserTenant (membership: invited_by, joined_at, is_active)
    │
    ├── schemas/
    │   ├── auth.py                  # LoginRequest, TokenResponse, TenantRegistration*
    │   ├── user.py                  # UserCreate, UserOutput, UserListItem, UserRoleInfo
    │   ├── tenant.py                # PlatformTenantCreate
    │   ├── role.py                  # RoleCreate, RoleOutPut, RoleDetail, RoleInfo, RolePermissionUpdate
    │   └── permission.py            # PermissionOutput
    │
    ├── repositories/
    │   ├── base_repo.py             # BaseRepository (holds Session)
    │   ├── user_repo.py             # UserRepo
    │   ├── user_tenant_repo.py      # UserTenantRepo
    │   ├── user_role_repo.py        # UserRoleRepo
    │   ├── tenant_repo.py           # TenantRepo
    │   ├── role_repo.py             # RoleRepo (get_system_role, get_by_id_in_tenant)
    │   └── permission_repo.py       # PermissionRepo
    │
    ├── services/
    │   ├── auth_service.py          # Login, token validation
    │   ├── user_service.py          # User creation, listing, role assignment/revocation
    │   ├── tenant_service.py        # Tenant provisioning (public + platform-admin paths)
    │   ├── role_service.py          # Role CRUD, permission-set management
    │   └── permission_service.py    # sync_permissions_global, list_permissions
    │
    ├── routers/
    │   ├── routes_v1.py             # Aggregates all v1 routers
    │   ├── admin/
    │   │   ├── auth.py              # POST /auth/login
    │   │   ├── users.py             # User CRUD + role assignment endpoints
    │   │   ├── tenants.py           # POST /platform/tenant/create (super admin)
    │   │   └── permissions.py       # POST /platform/permissions/sync (super admin)
    │   ├── tenant/
    │   │   ├── roles.py             # Role CRUD + permission-set management
    │   │   └── permissions.py       # GET /permissions/permission-list
    │   └── public/
    │       └── tenants.py           # POST /public/tenant/register (no auth)
    │
    ├── cli/
    │   ├── system_seed.py           # Step 1 — global permissions + system roles
    │   ├── platform_user.py         # Step 2 — platform super-admin user
    │   └── tenant_seed.py           # Step 3 — default tenant + tenant-admin user
    │
    └── utils/
        └── permission_marker.py     # @permission(code) decorator stub
```

---

## Architecture Overview

### Four-layer stack

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

### Request dependency chain for protected endpoints

```
Depends(get_current_user)            ← decodes JWT, loads User, checks is_active
Depends(get_tenant_context)          ← reads X-Tenant-ID header; super-admins bypass
Depends(require_permission("code"))  ← single JOIN: UserRole→Role→RolePermission→Permission
```

Super-admins short-circuit every check and are always allowed.

---

## Database Models

### `tenants`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7 |
| `name` | String(150) | Unique, indexed |
| `is_active` | Boolean | Default `True`, indexed |
| `created_at`, `updated_at`, `deleted_at` | DateTime(tz) | Via `TimestampMixin` |

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7 |
| `first_name`, `last_name` | String(255) | Nullable |
| `email` | String(255) | Unique, indexed |
| `password` | String(255) | Argon2 hash |
| `is_active` | Boolean | Default `False`, indexed |
| `is_verified` | Boolean | Default `False`, indexed |
| `is_super_admin` | Boolean | Default `False`, indexed |
| `verified_at` | DateTime(tz) | Nullable |
| `created_at`, `updated_at`, `deleted_at` | DateTime(tz) | |

### `permissions` — GLOBAL (no tenant scope)

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7 |
| `code` | String(150) | Globally unique, indexed (e.g. `user.create`) |
| `description` | String(255) | Nullable |
| `category` | String(50) | Nullable, indexed — auto-derived from the first dot segment of `code` |
| `scope` | String(20) | Default `"tenant"` |
| `created_at`, `updated_at`, `deleted_at` | DateTime(tz) | |

Permissions are **not** scoped to a tenant. One row per code, shared by all.

### `roles`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7 |
| `tenant_id` | UUID FK → `tenants` | **Nullable** — `NULL` = system role |
| `name` | String(100) | |
| `description` | String(255) | Nullable |
| `is_system` | Boolean | Default `False`; system roles cannot be modified via tenant API |
| `scope` | String(20) | Default `"tenant"` |
| `created_at`, `updated_at`, `deleted_at` | DateTime(tz) | |

**Unique constraints:**
- `(tenant_id, name)` — name unique within a tenant (`uq_role_tenant_name`)
- Partial unique index `uq_role_system_name` on `name WHERE tenant_id IS NULL` — enforces globally unique names for system roles

### `role_permissions` — M2M join

| Column | Type | Notes |
|---|---|---|
| `role_id` | UUID FK → `roles` CASCADE | Composite PK |
| `permission_id` | UUID FK → `permissions` CASCADE | Composite PK |

### `user_tenants` — membership

Links a user to a tenant. Role grants live in `user_roles`, NOT here.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7 |
| `user_id` | UUID FK → `users` CASCADE | Indexed |
| `tenant_id` | UUID FK → `tenants` CASCADE | Indexed |
| `invited_by` | UUID FK → `users` SET NULL | Nullable, indexed |
| `joined_at` | DateTime(tz) | Default `utcnow` |
| `is_active` | Boolean | Default `True`, indexed — soft-removal flag |
| Unique | `(user_id, tenant_id)` | `uq_user_tenant` |

### `user_roles` — role assignments (M2M)

A user can hold **multiple** roles inside a single tenant.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7 — surrogate key |
| `user_id` | UUID FK → `users` CASCADE | Indexed |
| `tenant_id` | UUID FK → `tenants` CASCADE | Indexed |
| `role_id` | UUID FK → `roles` CASCADE | Indexed |
| `granted_by` | UUID FK → `users` SET NULL | Nullable, indexed |
| `created_at`, `updated_at`, `deleted_at` | DateTime(tz) | |
| Unique | `(user_id, tenant_id, role_id)` | `uq_user_tenant_role` |

---

## Authentication & Authorization Flow

### 1. Login

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secret
```

Returns a **global JWT** containing `sub` (user UUID) and `is_super_admin`. The token is not bound to any tenant.

### 2. Authenticated Request

Send the token and desired tenant for every protected request:

```
GET /api/v1/users/list
Authorization: Bearer <token>
X-Tenant-ID: <tenant-uuid>
```

### 3. Authorization checks (in order)

1. **`get_current_user`** — decodes JWT, loads `User`, requires `is_active`.
2. **`get_tenant_context`** — validates `X-Tenant-ID`; requires a `UserTenant` row for non-super-admins.
3. **`require_permission("code")`** — single-JOIN query: `UserRole → Role → RolePermission → Permission`. Checks `UserTenant.is_active` (soft-removed members are blocked). Super-admins bypass.

### Password security

- Argon2 hashing via `passlib`.
- Passwords are capped at 72 UTF-8 bytes before hashing.

---

## Permission System

Permissions are defined **manually** in `app/core/permissions/definitions.py` as a list of `(code, description)` tuples. They are never auto-detected from routes.

```python
TENANT_PERMISSIONS = [
    ("user.create",  "Create user"),
    ("user.list",    "List users"),
    ("role.create",  "Create role"),
    ...
]
```

The `category` field is auto-derived at insert time from the first dot-segment of `code` (e.g. `user.create` → category `user`).

### System roles

Defined in `app/core/permissions/system_roles.py`:

| Role | Permissions |
|---|---|
| `admin` | All codes in `TENANT_PERMISSIONS` |
| `viewer` | `tenant.read`, `user.list`, `role.list` |
| `member` | `tenant.read` |

System roles have `tenant_id IS NULL` and `is_system = True`. They are seeded once and shared by every tenant. Tenant-scoped role endpoints block modifications to system roles (403).

### Adding a new permission — checklist

1. Add `("new.code", "Description")` to `definitions.py`.
2. Optionally add `"new.code"` to the relevant role in `system_roles.py`.
3. Re-run `python app/cli/system_seed.py` — idempotent, inserts new rows and reconciles system-role permission sets.
4. Wire the guard in the router: `dependencies=[Depends(require_permission("new.code"))]`.

Alternatively, hit `POST /api/v1/platform/permissions/sync` as a super-admin to do step 3 via HTTP.

---

## API Endpoints

All routes are mounted under `/api/v1`.

### Auth

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/auth/login` | None | Returns JWT |

### Public

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/public/tenant/register` | None | Self-service tenant + owner creation |

### Platform Admin (super-admin only)

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/platform/tenant/create` | JWT + `is_super_admin` | Create tenant + initial admin user |
| `POST` | `/platform/permissions/sync` | JWT + `is_super_admin` | Sync global permission catalog to DB |

### Users (tenant-scoped, require `X-Tenant-ID`)

| Method | Path | Permission | Notes |
|---|---|---|---|
| `POST` | `/users/create` | `user.create` | Create/attach user to tenant, grant roles |
| `GET` | `/users/list` | `user.list` | List active members with their roles |
| `GET` | `/users/me/roles` | — (any member) | Authenticated user's own roles in this tenant |
| `GET` | `/users/{user_id}/roles` | `user.list` | Any user's roles in this tenant |
| `POST` | `/users/{user_id}/roles/{role_id}` | `user.update` | Grant a role to a user (idempotent) |
| `DELETE` | `/users/{user_id}/roles/{role_id}` | `user.update` | Revoke a role from a user |

### Roles (tenant-scoped)

| Method | Path | Permission | Notes |
|---|---|---|---|
| `POST` | `/roles/create` | `role.create` | Create tenant-owned role, optionally assign permissions |
| `GET` | `/roles/list` | `role.list` | List all roles visible to this tenant (owned + system) |
| `GET` | `/roles/{role_id}` | `role.list` | Role detail with full permission list |
| `PUT` | `/roles/{role_id}/permissions` | `role.update` | Replace a role's entire permission set |
| `POST` | `/roles/{role_id}/permissions/{permission_id}` | `role.update` | Idempotently add one permission |
| `DELETE` | `/roles/{role_id}/permissions/{permission_id}` | `role.update` | Remove one permission |

> Permission-set management is blocked on system roles (returns 403).

### Permissions (tenant-scoped)

| Method | Path | Permission | Notes |
|---|---|---|---|
| `GET` | `/permissions/permission-list` | — (any member) | Browse the global permission catalog |

> **Interactive docs:** [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) and [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Environment Variables

Create a `.env` file in the project root.

```env
# Application
APP_NAME="FastAPI Multi Tenant Auth"
DEBUG=False
FRONTEND_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT
JWT_SECRET_KEY=your-very-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
EMAIL_TOKEN_EXPIRE_MINUTES=60

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

### CLI bootstrap variables (optional)

Read by the CLI scripts in `app/cli/`. If a `*_PASSWORD` variable is absent, the script prompts securely via `getpass`. Minimum password length is **8 characters**.

```env
# Step 2 — platform super-admin (app/cli/platform_user.py)
PLATFORM_ADMIN_EMAIL=admin@platform.com
PLATFORM_ADMIN_PASSWORD=

# Step 3 — default tenant + admin (app/cli/tenant_seed.py)
SEED_TENANT_NAME=default
SEED_TENANT_ADMIN_EMAIL=admin@tenant.com
SEED_TENANT_ADMIN_PASSWORD=
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

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env   # then edit DATABASE_URL, JWT_SECRET_KEY, etc.
```

### Database Setup

```bash
alembic upgrade head
```

> `alembic.ini` and `.env` must both point to the same `DATABASE_URL`.

### Bootstrap — required order

These three scripts are **idempotent** (safe to re-run) and must be executed **in order** after a fresh migration.

```bash
# Step 1 — insert global permission catalog + create system roles (admin / member / viewer)
python app/cli/system_seed.py

# Step 2 — create the platform super-admin user
# Supply password via env var or let the script prompt:
PLATFORM_ADMIN_PASSWORD='your-secure-password' python app/cli/platform_user.py

# Step 3 — create the default tenant + tenant-admin user, grant the system admin role
SEED_TENANT_ADMIN_PASSWORD='your-secure-password' python app/cli/tenant_seed.py
```

**Why order matters:**

- `system_seed.py` must run first — it creates the global `admin` system role.
- `tenant_seed.py` requires the system `admin` role to exist and will exit cleanly if it is missing.
- `platform_user.py` is independent of the other two but makes sense after the schema is ready.

### Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## Known Caveats

| Issue | Location | Detail |
|---|---|---|
| **Broad `except Exception` in some routers** | `app/routers/**/*.py` | Several handlers catch `Exception` and re-raise as 500. This can swallow descriptive `HTTPException` messages raised by services. Narrow to `except HTTPException: raise` first. |
| **Mail settings required** | `app/core/config/settings.py` | All `MAIL_*` variables must be present in `.env` even though no mailer is wired to any endpoint. Make them `Optional[str] = None` to relax this requirement. |
| **No CORS / rate limiting** | `main.py`, `app/routers/public/tenants.py` | Add `CORSMiddleware` for SPA clients and rate-limit the public registration endpoint before exposing publicly. |
| **Tenant-admin `is_active` default** | `app/models/user.py` | `User.is_active` defaults to `False` at the model level, but the CLI scripts and services set it to `True` explicitly when creating seeded/registered users. New users created via `POST /users/create` inherit the `True` override in `UserService`. |
