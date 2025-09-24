from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.queue.models import CustomerStatus, QueueStatus


# Queue Schemas
class QueueBase(BaseModel):
    name: str
    description: Optional[str] = None
    service_id: Optional[UUID] = None
    location_id: UUID
    max_capacity: Optional[int] = None
    estimated_service_time: Optional[int] = None

    # Event/Mobile queue fields
    event_name: Optional[str] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    is_mobile_queue: bool = False


class QueueCreate(QueueBase):
    pass


class QueueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[QueueStatus] = None
    max_capacity: Optional[int] = None
    estimated_service_time: Optional[int] = None
    is_active: Optional[bool] = None

    # Event/Mobile queue fields
    event_name: Optional[str] = None
    event_start_date: Optional[datetime] = None
    event_end_date: Optional[datetime] = None
    is_mobile_queue: Optional[bool] = None


class Queue(QueueBase):
    queue_id: UUID
    status: QueueStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QueueResponse(QueueBase):
    queue_id: UUID
    status: QueueStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    service_name: Optional[str] = None

    # Computed fields
    current_size: int = 0
    waiting_customers: int = 0

    class Config:
        from_attributes = True


# QueueCustomer Schemas
class QueueCustomerBase(BaseModel):
    queue_id: UUID
    user_id: Optional[UUID] = None
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
    queue_customer_id: UUID
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
    user_id: Optional[UUID] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    party_size: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class QueuePositionResponse(BaseModel):
    queue_customer_id: UUID
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
    queue_id: UUID


class QueueStatusResponse(BaseModel):
    queue_id: UUID
    name: str
    status: QueueStatus
    current_size: int
    waiting_customers: int
    average_wait_time: Optional[int] = None
    is_accepting_customers: bool


# Wizard schemas for creating queue + service + location
class WizardNewService(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None  # This matches ServiceBase
    price: Optional[float] = None
    is_active: bool = True
    max_daily_capacity: Optional[int] = None


class WizardServiceConfig(BaseModel):
    useExisting: bool = False
    existingServiceId: Optional[UUID] = None
    newService: Optional[WizardNewService] = None

    @field_validator("existingServiceId", mode="before")
    @classmethod
    def validate_existing_service_id(cls, v):
        if v == "" or v is None:
            return None
        return v


class WizardNewLocation(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "NL"
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class WizardLocationConfig(BaseModel):
    useExisting: bool
    existingLocationId: Optional[UUID] = None
    newLocation: Optional[WizardNewLocation] = None

    @field_validator("existingLocationId", mode="before")
    @classmethod
    def validate_existing_location_id(cls, v):
        if v == "" or v is None:
            return None
        return v


class WizardQueueConfig(BaseModel):
    name: str
    description: Optional[str] = None
    max_capacity: Optional[int] = None
    estimated_service_time: Optional[int] = None


class QueueWizardRequest(BaseModel):
    queue: WizardQueueConfig
    service: WizardServiceConfig
    location: WizardLocationConfig

    def model_validate(cls, v):
        # Validate service config
        if v.service.useExisting and not v.service.existingServiceId:
            raise ValueError(
                "existingServiceId is required when useExisting is true for service"
            )
        # Note: newService is optional since new service creation is currently disabled
        # if not v.service.useExisting and not v.service.newService:
        #     raise ValueError(
        #         "newService data is required when useExisting is false for service"
        #     )

        # Validate location config
        if v.location.useExisting and not v.location.existingLocationId:
            raise ValueError(
                "existingLocationId is required when useExisting is true for location"
            )
        if not v.location.useExisting and not v.location.newLocation:
            raise ValueError(
                "newLocation data is required when useExisting is false for location"
            )

        return v


class QueueWizardResponse(BaseModel):
    queue_id: UUID
    queue_name: str
    service_id: Optional[UUID] = None
    service_name: Optional[str] = None
    location_id: UUID
    location_name: str
    created_new_service: bool
    created_new_location: bool
