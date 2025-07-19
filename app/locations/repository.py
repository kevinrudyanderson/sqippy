from typing import List, Optional

from sqlalchemy.orm import Session

from app.base.repositories import BaseRepository
from app.locations.models import Location
from app.queue.models import Queue


class LocationRepository(BaseRepository[Location]):
    def __init__(self, db: Session):
        super().__init__(db, Location)

    def get_queues_by_location(self, location_id: str) -> List[Queue]:
        return self.db.query(Queue).filter(Queue.location_id == location_id).all()

    # Organization-based methods (much simpler!)
    def get_by_organization(self, organization_id: str, skip: int = 0, limit: int = 100) -> List[Location]:
        """Get all locations for an organization"""
        return self.db.query(Location).filter(
            Location.organization_id == organization_id
        ).offset(skip).limit(limit).all()

    def get_organization_location(self, location_id: str, organization_id: str) -> Optional[Location]:
        """Get a specific location if it belongs to the organization"""
        return self.db.query(Location).filter(
            Location.location_id == location_id,
            Location.organization_id == organization_id
        ).first()
