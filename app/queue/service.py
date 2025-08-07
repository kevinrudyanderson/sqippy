from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.queue.models import CustomerStatus, Queue, QueueCustomer, QueueStatus
from app.queue.repository import QueueCustomerRepository, QueueRepository
from app.queue.schemas import (
    AddCustomerToQueueRequest,
    QueueCreate,
    QueuePositionResponse,
    QueueResponse,
    QueueStatusResponse,
    QueueUpdate,
)


class QueueService:
    def __init__(self, db: Session):
        self.db = db
        self.queue_repo = QueueRepository(db)
        self.customer_repo = QueueCustomerRepository(db)
    
    def create_queue(self, queue_data: QueueCreate) -> Queue:
        # Verify location exists (would need location repository)
        # For now, we'll assume location is valid
        
        queue = Queue(**queue_data.model_dump())
        return self.queue_repo.create(queue)
    
    def get_queue(self, queue_id: str) -> Queue:
        queue = self.queue_repo.get(queue_id)
        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue not found"
            )
        return queue
    
    def update_queue(self, queue_id: str, update_data: QueueUpdate) -> Queue:
        queue = self.get_queue(queue_id)
        return self.queue_repo.update_from_schema(queue, update_data)
    
    def delete_queue(self, queue_id: str) -> Queue:
        queue = self.get_queue(queue_id)
        
        # Check if there are active customers
        active_customers = self.customer_repo.get_queue_customers(
            queue_id, 
            status=CustomerStatus.WAITING
        )
        if active_customers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete queue with active customers"
            )
        
        queue.is_active = False
        return self.queue_repo.update(queue)
    
    def get_queues_by_location(self, location_id: str) -> List[Queue]:
        return self.queue_repo.get_by_location(location_id)
    
    def get_queues_by_service(self, service_id: str) -> List[Queue]:
        return self.queue_repo.get_by_service(service_id)
    
    def get_queue_customer(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        return self.customer_repo.get(queue_customer_id)
    
    def add_customer_to_queue(
        self, 
        queue_id: str, 
        customer_data: AddCustomerToQueueRequest
    ) -> QueueCustomer:
        # Verify queue exists and is active
        queue = self.get_queue(queue_id)
        if queue.status != QueueStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Queue is not accepting new customers"
            )
        
        # Check if queue is at capacity
        if queue.max_capacity:
            current_size = len(self.customer_repo.get_waiting_customers(queue_id))
            if current_size >= queue.max_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Queue is at maximum capacity"
                )
        
        # Validate customer data
        if not customer_data.user_id and not customer_data.customer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either user_id or customer_name must be provided"
            )
        
        # Create customer entry
        customer = QueueCustomer(
            queue_id=queue_id,
            **customer_data.model_dump()
        )
        
        return self.customer_repo.add_customer_to_queue(customer)
    
    def get_queue_status(self, queue_id: str) -> QueueStatusResponse:
        queue = self.get_queue(queue_id)
        
        waiting_customers = self.customer_repo.get_waiting_customers(queue_id)
        in_service_customers = self.customer_repo.get_queue_customers(
            queue_id, 
            CustomerStatus.IN_SERVICE
        )
        
        # Calculate average wait time based on recent completions
        # This is a simplified implementation
        average_wait_time = None
        if queue.estimated_service_time and waiting_customers:
            average_wait_time = queue.estimated_service_time * len(waiting_customers)
        
        return QueueStatusResponse(
            queue_id=queue.queue_id,
            name=queue.name,
            status=queue.status,
            current_size=len(waiting_customers) + len(in_service_customers),
            waiting_customers=len(waiting_customers),
            average_wait_time=average_wait_time,
            is_accepting_customers=(queue.status == QueueStatus.ACTIVE)
        )
    
    def get_customer_position(self, queue_customer_id: str) -> QueuePositionResponse:
        customer = self.customer_repo.get(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in queue"
            )
        
        queue = self.queue_repo.get(customer.queue_id)
        
        # Handle different customer statuses
        if customer.status == CustomerStatus.WAITING:
            position = self.customer_repo.get_customer_position(queue_customer_id)
            ahead_in_queue = position - 1 if position else 0
            estimated_wait_time = None
            if queue.estimated_service_time and position and position > 0:
                estimated_wait_time = queue.estimated_service_time * (position - 1)
            status_message = f"You are #{position} in line. {ahead_in_queue} people ahead of you."
        elif customer.status == CustomerStatus.IN_SERVICE:
            position = None
            ahead_in_queue = None  
            estimated_wait_time = 0
            status_message = "You have been called! It's your turn - please proceed to the service area."
        elif customer.status == CustomerStatus.COMPLETED:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = "Your service has been completed. Thank you!"
        elif customer.status == CustomerStatus.CANCELLED:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = "Your queue entry has been cancelled."
        elif customer.status == CustomerStatus.NO_SHOW:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = "You were called but did not respond. Your queue entry has been marked as no-show."
        else:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = f"Your current status: {customer.status.value}"
        
        # Get customer info from registered user if available
        customer_name = customer.customer_name
        customer_email = customer.customer_email  
        customer_phone = customer.customer_phone
        
        # If customer is a registered user, use their profile info as fallback
        if customer.user_id and customer.user:
            customer_name = customer_name or customer.user.name
            customer_email = customer_email or customer.user.email
            customer_phone = customer_phone or customer.user.phone_number
        
        return QueuePositionResponse(
            queue_customer_id=queue_customer_id,
            position=position,
            ahead_in_queue=ahead_in_queue,
            estimated_wait_time=estimated_wait_time,
            status=customer.status.value,
            status_message=status_message,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            party_size=customer.party_size,
            queue_name=queue.name,
            queue_id=queue.queue_id
        )
    
    def call_next_customer(self, queue_id: str) -> Optional[QueueCustomer]:
        queue = self.get_queue(queue_id)
        return self.customer_repo.call_next_customer(queue_id)
    
    def complete_customer(self, queue_customer_id: str) -> QueueCustomer:
        customer = self.customer_repo.complete_customer(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found or not in service"
            )
        return customer
    
    def cancel_customer(self, queue_customer_id: str) -> QueueCustomer:
        customer = self.customer_repo.cancel_customer(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found or cannot be cancelled"
            )
        return customer
    
    def get_queue_customers(
        self, 
        queue_id: str, 
        status: Optional[CustomerStatus] = None
    ) -> List[QueueCustomer]:
        self.get_queue(queue_id)  # Verify queue exists
        return self.customer_repo.get_queue_customers(queue_id, status)
    
    def get_user_accessible_queues(self, user_id: str) -> List[Queue]:
        """Get all active queues in the user's organization"""
        return self.queue_repo.get_organization_queues(user_id)