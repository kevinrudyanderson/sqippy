from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.base.repositories import BaseRepository
from app.queue.models import CustomerStatus, Queue, QueueCustomer, QueueStatus


class QueueRepository(BaseRepository[Queue]):
    def __init__(self, db: Session):
        super().__init__(db, Queue)
    
    def get_by_id(self, queue_id: str) -> Optional[Queue]:
        return self.db.query(Queue).filter(Queue.queue_id == queue_id).first()
    
    def get_by_location(self, location_id: str) -> List[Queue]:
        return self.db.query(Queue).filter(
            Queue.location_id == location_id,
            Queue.is_active == True
        ).all()
    
    def get_active_queues(self) -> List[Queue]:
        return self.db.query(Queue).filter(
            Queue.status == QueueStatus.ACTIVE,
            Queue.is_active == True
        ).all()


class QueueCustomerRepository(BaseRepository[QueueCustomer]):
    def __init__(self, db: Session):
        super().__init__(db, QueueCustomer)
    
    def get_by_id(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        return self.db.query(QueueCustomer).filter(
            QueueCustomer.queue_customer_id == queue_customer_id
        ).first()
    
    def add_customer_to_queue(self, customer: QueueCustomer) -> QueueCustomer:
        # No need to set position - joined_at is automatically set
        return self.create(customer)
    
    def get_queue_customers(
        self, 
        queue_id: str, 
        status: Optional[CustomerStatus] = None
    ) -> List[QueueCustomer]:
        query = self.db.query(QueueCustomer).filter(
            QueueCustomer.queue_id == queue_id
        )
        
        if status:
            query = query.filter(QueueCustomer.status == status)
        
        return query.order_by(QueueCustomer.joined_at).all()
    
    def get_waiting_customers(self, queue_id: str) -> List[QueueCustomer]:
        return self.get_queue_customers(queue_id, CustomerStatus.WAITING)
    
    def get_customer_position(self, queue_customer_id: str) -> Optional[int]:
        customer = self.get_by_id(queue_customer_id)
        if not customer or customer.status != CustomerStatus.WAITING:
            return None
        
        # Count customers ahead in queue (joined earlier)
        ahead_count = self.db.query(QueueCustomer).filter(
            QueueCustomer.queue_id == customer.queue_id,
            QueueCustomer.status == CustomerStatus.WAITING,
            QueueCustomer.joined_at < customer.joined_at
        ).count()
        
        return ahead_count + 1
    
    def call_next_customer(self, queue_id: str) -> Optional[QueueCustomer]:
        # Get the next waiting customer (earliest joined_at)
        next_customer = self.db.query(QueueCustomer).filter(
            QueueCustomer.queue_id == queue_id,
            QueueCustomer.status == CustomerStatus.WAITING
        ).order_by(QueueCustomer.joined_at).first()
        
        if next_customer:
            next_customer.status = CustomerStatus.IN_SERVICE
            next_customer.called_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(next_customer)
        
        return next_customer
    
    def complete_customer(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        customer = self.get_by_id(queue_customer_id)
        if customer and customer.status == CustomerStatus.IN_SERVICE:
            customer.status = CustomerStatus.COMPLETED
            customer.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(customer)
            return customer
        return None
    
    def cancel_customer(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        customer = self.get_by_id(queue_customer_id)
        if customer and customer.status in [CustomerStatus.WAITING, CustomerStatus.IN_SERVICE]:
            customer.status = CustomerStatus.CANCELLED
            customer.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(customer)
            return customer
        return None