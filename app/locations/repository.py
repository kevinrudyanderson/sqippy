from typing import List

from sqlalchemy.orm import Session

from app.base.repositories import BaseRepository
from app.locations.models import Location
from app.queue.models import Queue


class LocationRepository(BaseRepository[Location]):
    def __init__(self, db: Session):
        super().__init__(db, Location)

    def get_queues_by_location(self, location_id: str) -> List[Queue]:
        return self.db.query(Queue).filter(Queue.location_id == location_id).all()
