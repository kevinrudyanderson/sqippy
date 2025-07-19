from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.models import User
from app.auth.roles import UserRole
from app.organizations.dependencies import (
    get_organization_service,
    require_organization_admin,
    get_organization_context,
    OrganizationContext
)
from app.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationSummary,
    OrganizationUpdate,
)
from app.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    organization_data: OrganizationCreate,
    current_user: User = Depends(require_organization_admin),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Create a new organization (Admin+ only)"""
    # Only super admins can create organizations
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can create organizations"
        )
    
    organization = organization_service.create_organization(organization_data)
    return OrganizationResponse(**organization.__dict__)


@router.get("/", response_model=List[OrganizationSummary])
async def get_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, min_length=1),
    current_user: User = Depends(require_organization_admin),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Get organizations (Super admin sees all, others see only their own)"""
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        if search:
            organizations = organization_service.search_organizations(search, skip, limit)
        else:
            organizations = organization_service.get_organizations(skip, limit)
    else:
        # Regular admins can only see their own organization
        if not current_user.organization_id:
            return []
        organization = organization_service.get_organization(current_user.organization_id)
        organizations = [organization]
    
    return [OrganizationSummary(**org.__dict__) for org in organizations]


@router.get("/me", response_model=OrganizationResponse)
async def get_my_organization(
    context: OrganizationContext = Depends(get_organization_context),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Get current user's organization"""
    organization = organization_service.get_organization(context.organization_id)
    return OrganizationResponse(**organization.__dict__)


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str,
    current_user: User = Depends(require_organization_admin),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Get organization by ID"""
    # Super admin can access any organization, others only their own
    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    organization = organization_service.get_organization(organization_id)
    return OrganizationResponse(**organization.__dict__)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: str,
    update_data: OrganizationUpdate,
    current_user: User = Depends(require_organization_admin),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Update organization"""
    # Super admin can update any organization, others only their own
    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization"
        )
    
    organization = organization_service.update_organization(organization_id, update_data)
    return OrganizationResponse(**organization.__dict__)


@router.delete("/{organization_id}", response_model=OrganizationResponse)
async def delete_organization(
    organization_id: str,
    current_user: User = Depends(require_organization_admin),
    organization_service: OrganizationService = Depends(get_organization_service),
):
    """Soft delete organization (Super admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete organizations"
        )
    
    organization = organization_service.delete_organization(organization_id)
    return OrganizationResponse(**organization.__dict__)