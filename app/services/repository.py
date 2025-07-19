from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.base.repositories import BaseRepository
from app.services.models import Service
from app.locations.models import Location


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, db: Session):
        super().__init__(db, Service)

    def get_by_location(self, location_id: str) -> List[Service]:
        """Get all services for a specific location."""
        return (
            self.db.query(Service)
            .filter(Service.location_id == location_id, Service.is_active == True)
            .all()
        )

    def get_by_category(self, category: str) -> List[Service]:
        """Get all services by category."""
        return (
            self.db.query(Service)
            .filter(Service.category == category, Service.is_active == True)
            .all()
        )

    def get_active_services(self) -> List[Service]:
        """Get all active services."""
        return self.db.query(Service).filter(Service.is_active == True).all()

    # Organization-based methods (much simpler!)
    def get_by_organization(self, organization_id: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Get all services for an organization through locations"""
        return self.db.query(Service).join(Location, Service.location_id == Location.location_id).filter(
            and_(
                Location.organization_id == organization_id,
                Service.is_active == True
            )
        ).offset(skip).limit(limit).all()

    def get_organization_service(self, service_id: str, organization_id: str) -> Optional[Service]:
        """Get a specific service if it belongs to the organization"""
        return self.db.query(Service).join(Location, Service.location_id == Location.location_id).filter(
            and_(
                Service.service_id == service_id,
                Location.organization_id == organization_id
            )
        ).first()
    
    def get_by_organization_and_id(self, service_id: str, organization_id: str) -> Optional[Service]:
        """Alias for get_organization_service for consistency"""
        return self.get_organization_service(service_id, organization_id)
    
    def get_by_category_and_organization(self, category: str, organization_id: str) -> List[Service]:
        """Get services by category within an organization"""
        return self.db.query(Service).join(Location, Service.location_id == Location.location_id).filter(
            and_(
                Service.category == category,
                Location.organization_id == organization_id,
                Service.is_active == True
            )
        ).all()
