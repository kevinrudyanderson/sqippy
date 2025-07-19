from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.locations.dependencies import get_location_repository
from app.locations.schemas import AddLocationRequest, LocationResponse
from app.locations.service import LocationService
from app.locations.repository import LocationRepository
from app.organizations.dependencies import (
    get_organization_context,
    OrganizationContext
)
from app.database import get_db

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/", response_model=LocationResponse)
def create_location(
    location: AddLocationRequest,
    org_context: OrganizationContext = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    """Create a new location - any organization member can create"""
    location_service = LocationService(db)
    
    # Create location data with organization ID
    from app.locations.models import Location
    new_location = Location(
        organization_id=org_context.organization_id,
        **location.model_dump()
    )
    
    created_location = location_service.location_repo.create(new_location)
    return LocationResponse.model_validate(created_location)


@router.get("/debug/{location_id}")
def debug_location_access(
    location_id: str,
    org_context: OrganizationContext = Depends(get_organization_context),
    db: Session = Depends(get_db)
):
    """Debug endpoint to check organization access to a location"""
    location_repo = LocationRepository(db)
    location = location_repo.get(location_id)
    
    return {
        "user_id": org_context.user.user_id,
        "organization_id": org_context.organization_id,
        "location_id": location_id,
        "location_exists": location is not None,
        "location_organization_id": location.organization_id if location else None,
        "same_organization": location.organization_id == org_context.organization_id if location else False,
        "can_access": location is not None and location.organization_id == org_context.organization_id
    }


@router.get("/", response_model=List[LocationResponse])
def get_locations(
    skip: int = 0,
    limit: int = 100,
    org_context: OrganizationContext = Depends(get_organization_context),
    location_repo: LocationRepository = Depends(get_location_repository)
):
    """Get all locations for the user's organization"""
    if org_context.can_access_all_organizations():
        # Super admin can see all locations
        locations = location_repo.get_all(skip, limit)
    else:
        # Regular users see all locations in their organization
        locations = location_repo.get_by_organization(
            org_context.organization_id, 
            skip, 
            limit
        )
    
    return [LocationResponse.model_validate(location) for location in locations]


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: str,
    org_context: OrganizationContext = Depends(get_organization_context),
    location_repo: LocationRepository = Depends(get_location_repository)
):
    """Get a specific location if it belongs to user's organization"""
    if org_context.can_access_all_organizations():
        location = location_repo.get(location_id)
    else:
        location = location_repo.get_organization_location(
            location_id, 
            org_context.organization_id
        )
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or access denied"
        )
    
    return LocationResponse.model_validate(location)
