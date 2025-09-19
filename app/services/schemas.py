from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.queue.schemas import Queue


class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    is_active: bool = True
    max_daily_capacity: Optional[int] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
    max_daily_capacity: Optional[int] = None


class ServiceInDBBase(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    service_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class Service(ServiceInDBBase):
    pass


class ServiceWithQueues(ServiceInDBBase):
    queues: List[Queue] = []
