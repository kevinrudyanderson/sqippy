from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.queue.models import CustomerStatus, QueueStatus


# Queue Schemas
class QueueBase(BaseModel):
    name: str
    description: Optional[str] = None
    service_id: str
    max_capacity: Optional[int] = None
    estimated_service_time: Optional[int] = None


class QueueCreate(QueueBase):
    pass


class QueueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[QueueStatus] = None
    max_capacity: Optional[int] = None
    estimated_service_time: Optional[int] = None
    is_active: Optional[bool] = None


class Queue(QueueBase):
    queue_id: str
    status: QueueStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QueueResponse(QueueBase):
    queue_id: str
    status: QueueStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    current_size: int = 0
    waiting_customers: int = 0

    class Config:
        from_attributes = True


# QueueCustomer Schemas
class QueueCustomerBase(BaseModel):
    queue_id: str
    user_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    party_size: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class QueueCustomerCreate(QueueCustomerBase):
    pass


class QueueCustomerUpdate(BaseModel):
    status: Optional[CustomerStatus] = None
    notes: Optional[str] = None
    party_size: Optional[int] = Field(None, ge=1)


class QueueCustomerResponse(QueueCustomerBase):
    queue_customer_id: str
    status: CustomerStatus
    joined_at: datetime
    called_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    position: Optional[int] = None  # Calculated dynamically based on joined_at
    estimated_wait_time: Optional[int] = None  # in minutes

    class Config:
        from_attributes = True


# Additional schemas for queue operations
class AddCustomerToQueueRequest(BaseModel):
    user_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    party_size: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class QueuePositionResponse(BaseModel):
    queue_customer_id: str
    position: Optional[int] = None  # Null when not waiting
    ahead_in_queue: Optional[int] = None  # Null when not waiting
    estimated_wait_time: Optional[int] = None
    
    # Status information
    status: str  # "waiting", "in_service", "completed", "cancelled", "no_show"
    status_message: str  # Human-readable status message
    
    # Customer information
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    party_size: int = 1
    
    # Queue information
    queue_name: str
    queue_id: str


class QueueStatusResponse(BaseModel):
    queue_id: str
    name: str
    status: QueueStatus
    current_size: int
    waiting_customers: int
    average_wait_time: Optional[int] = None
    is_accepting_customers: bool