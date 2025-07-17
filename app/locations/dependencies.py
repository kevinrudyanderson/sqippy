from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.locations.repository import LocationRepository
from app.locations.service import LocationService


def get_location_repository(db: Session = Depends(get_db)) -> LocationRepository:
    return LocationRepository(db)


def get_location_service(db: Session = Depends(get_db)) -> LocationService:
    return LocationService(db)
