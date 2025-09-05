from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.queue.schemas import Queue


class AddLocationRequest(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "NL"
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class LocationResponse(BaseModel):
    location_id: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "NL"
    longitude: float
    latitude: float
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateLocationRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    is_active: Optional[bool] = None


class LocationWithQueues(LocationResponse):
    queues: List[Queue] = []
