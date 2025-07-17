from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.queue.repository import QueueCustomerRepository, QueueRepository
from app.queue.service import QueueService


def get_queue_repository(db: Session = Depends(get_db)) -> QueueRepository:
    return QueueRepository(db)


def get_queue_customer_repository(db: Session = Depends(get_db)) -> QueueCustomerRepository:
    return QueueCustomerRepository(db)


def get_queue_service(db: Session = Depends(get_db)) -> QueueService:
    return QueueService(db)