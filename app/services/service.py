from typing import List, Optional
from sqlalchemy.orm import Session

from app.services.models import Service
from app.services.repository import ServiceRepository
from app.services.schemas import ServiceCreate, ServiceUpdate


class ServiceService:
    def __init__(self, db: Session):
        self.repository = ServiceRepository(db)
    
    def create_service(self, service_data: ServiceCreate) -> Service:
        """Create a new service."""
        service = Service(**service_data.model_dump())
        return self.repository.create(service)
    
    def get_service(self, service_id: str) -> Optional[Service]:
        """Get a service by ID."""
        return self.repository.get(service_id)
    
    def get_services_by_location(self, location_id: str) -> List[Service]:
        """Get all services for a location."""
        return self.repository.get_by_location(location_id)
    
    def get_services_by_category(self, category: str) -> List[Service]:
        """Get all services by category."""
        return self.repository.get_by_category(category)
    
    def get_active_services(self) -> List[Service]:
        """Get all active services."""
        return self.repository.get_active_services()
    
    def update_service(self, service_id: str, service_update: ServiceUpdate) -> Optional[Service]:
        """Update a service."""
        service = self.repository.get(service_id)
        if service:
            return self.repository.update(service, service_update)
        return None
    
    def delete_service(self, service_id: str) -> bool:
        """Soft delete a service."""
        service = self.repository.get(service_id)
        if service:
            service_update = ServiceUpdate(is_active=False)
            self.repository.update(service, service_update)
            return True
        return False