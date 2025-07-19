from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.base.repositories import BaseRepository
from app.organizations.models import Organization


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: Session):
        super().__init__(db, Organization)
    
    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name"""
        return self.db.query(Organization).filter(
            Organization.name == name,
            Organization.is_active == True
        ).first()
    
    def get_active_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all active organizations"""
        return self.db.query(Organization).filter(
            Organization.is_active == True
        ).offset(skip).limit(limit).all()
    
    def search_by_name(self, name_query: str, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Search organizations by name (case-insensitive)"""
        return self.db.query(Organization).filter(
            and_(
                Organization.name.ilike(f"%{name_query}%"),
                Organization.is_active == True
            )
        ).offset(skip).limit(limit).all()
    
    def deactivate(self, organization_id: str) -> Optional[Organization]:
        """Soft delete organization by setting is_active to False"""
        organization = self.get(organization_id)
        if organization:
            organization.is_active = False
            self.db.commit()
            self.db.refresh(organization)
        return organization