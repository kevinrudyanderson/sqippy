from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel

from app.base.repositories import BaseRepository
from app.organizations.models import Organization


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: Session):
        super().__init__(db, Organization)
    
    def update_from_schema(self, obj: Organization, update_schema: BaseModel) -> Organization:
        """
        Override to add extra protection for critical fields.
        Prevents modification of plan, billing, and credit fields.
        """
        # Fields that should NEVER be updated through normal API endpoints
        PROTECTED_FIELDS = {
            'plan_type', 'plan_started_at', 'plan_expires_at',
            'stripe_customer_id', 'stripe_subscription_id',
            'sms_credits_total', 'sms_credits_used',
            'organization_id', 'created_at'
        }
        
        update_data = update_schema.model_dump(exclude_unset=True)
        schema_fields = set(update_schema.__class__.model_fields.keys())
        
        for field, value in update_data.items():
            # Skip protected fields even if they somehow appear in the data
            if field in PROTECTED_FIELDS:
                continue
            # Only update if field is defined in the schema AND exists on the object
            if field in schema_fields and hasattr(obj, field):
                setattr(obj, field, value)
        
        return self.update(obj)
    
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