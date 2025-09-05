from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.base.repositories import BaseRepository
from app.locations.models import Location
from app.services.models import Service


class ServiceRepository(BaseRepository[Service]):
    def __init__(self, db: Session):
        super().__init__(db, Service)

    def get_by_location(self, location_id: str) -> List[Service]:
        """Get all services available at a location (services are now global)."""
        # Since services are now global, return all active services
        return self.get_active_services()

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
    def get_by_organization(
        self, organization_id: str, skip: int = 0, limit: int = 100
    ) -> List[Service]:
        """Get all services for an organization (services are now global)."""
        # Since services are now global, return all active services
        return (
            self.db.query(Service)
            .filter(Service.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_organization_service(
        self, service_id: str, organization_id: str
    ) -> Optional[Service]:
        """Get a specific service (services are now global)."""
        # Since services are now global, just return the service if it exists and is active
        return (
            self.db.query(Service)
            .filter(and_(Service.service_id == service_id, Service.is_active == True))
            .first()
        )

    def get_by_organization_and_id(
        self, service_id: str, organization_id: str
    ) -> Optional[Service]:
        """Alias for get_organization_service for consistency"""
        return self.get_organization_service(service_id, organization_id)

    def get_by_category_and_organization(
        self, category: str, organization_id: str
    ) -> List[Service]:
        """Get services by category (services are now global)."""
        # Since services are now global, just filter by category
        return self.get_by_category(category)
