from sqlalchemy.orm import Session

from app.locations.models import Location
from app.locations.repository import LocationRepository
from app.locations.schemas import AddLocationRequest


class LocationService:
    def __init__(self, db: Session):
        self.db = db
        self.location_repo = LocationRepository(db)

    def create(self, location: AddLocationRequest) -> Location:
        return self.location_repo.create(Location(**location.model_dump()))

    def get_location(self, location_id: str) -> Location:
        return self.location_repo.get_by_id(location_id)
