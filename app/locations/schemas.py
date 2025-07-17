from typing import Optional

from pydantic import BaseModel


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
    postal_code: Optional[str] = None
    country: Optional[str] = "NL"
    longitude: Optional[float] = None
    latitude: Optional[float] = None
