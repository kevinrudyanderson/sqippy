from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.repository import ServiceRepository
from app.services.service import ServiceService


def get_service_repository(db: Session = Depends(get_db)) -> ServiceRepository:
    return ServiceRepository(db)


def get_service_service(db: Session = Depends(get_db)) -> ServiceService:
    return ServiceService(db)