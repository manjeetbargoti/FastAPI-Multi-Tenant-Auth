from app.repositories.base_repo import BaseRepository
from app.models.tenant import Tenant

class TenantRepo(BaseRepository):

    def add(self, tenant: Tenant) -> Tenant:
        self.db.add(tenant)
        return tenant
    
    def create(self, name: str) -> Tenant:
        tenant = Tenant(name=name)
        self.db.add(instance=tenant)
        self.db.flush()
        return tenant
    
    def get_by_name(self, name: str) -> Tenant | None:
        return self.db.query(Tenant).filter(Tenant.name == name).first()
    
    def get_all(self):
        return self.db.query(Tenant).all()
    
    def get_by_id(self, tenant_id: str):
        return self.db.get(Tenant, tenant_id)
    