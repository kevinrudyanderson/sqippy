from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("NL", max_length=10)


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization (all fields optional)"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=10)


class OrganizationResponse(OrganizationBase):
    """Schema for organization responses"""

    organization_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizationSummary(BaseModel):
    """Lightweight organization summary"""

    organization_id: UUID
    name: str
    business_type: Optional[str]
    city: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True
