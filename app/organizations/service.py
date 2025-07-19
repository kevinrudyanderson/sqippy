from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.organizations.models import Organization
from app.organizations.repository import OrganizationRepository
from app.organizations.schemas import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    def __init__(self, db: Session):
        self.db = db
        self.organization_repo = OrganizationRepository(db)
    
    def create_organization(self, organization_data: OrganizationCreate) -> Organization:
        """Create a new organization"""
        # Check if organization name already exists
        existing = self.organization_repo.get_by_name(organization_data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this name already exists"
            )
        
        organization = Organization(**organization_data.model_dump())
        return self.organization_repo.create(organization)
    
    def get_organization(self, organization_id: str) -> Organization:
        """Get organization by ID"""
        organization = self.organization_repo.get(organization_id)
        if not organization or not organization.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        return organization
    
    def get_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all active organizations (super admin only)"""
        return self.organization_repo.get_active_organizations(skip, limit)
    
    def search_organizations(self, name_query: str, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Search organizations by name"""
        return self.organization_repo.search_by_name(name_query, skip, limit)
    
    def update_organization(self, organization_id: str, update_data: OrganizationUpdate) -> Organization:
        """Update organization"""
        organization = self.get_organization(organization_id)
        
        # Check if name is being changed and if it conflicts
        if update_data.name and update_data.name != organization.name:
            existing = self.organization_repo.get_by_name(update_data.name)
            if existing and existing.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this name already exists"
                )
        
        return self.organization_repo.update_from_schema(organization, update_data)
    
    def delete_organization(self, organization_id: str) -> Organization:
        """Soft delete organization"""
        organization = self.get_organization(organization_id)
        
        # Check if organization has active users or locations
        if organization.users:
            active_users = [u for u in organization.users if u.is_active]
            if active_users:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete organization with active users"
                )
        
        if organization.locations:
            active_locations = [l for l in organization.locations if l.is_active]
            if active_locations:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete organization with active locations"
                )
        
        result = self.organization_repo.deactivate(organization_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        return result