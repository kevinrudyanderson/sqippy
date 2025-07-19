from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.access.models import AccessLevel, UserLocationAccess
from app.base.repositories import BaseRepository


class UserLocationAccessRepository(BaseRepository[UserLocationAccess]):
    def __init__(self, db: Session):
        super().__init__(db, UserLocationAccess)

    def get_user_access(
        self, user_id: str, location_id: str
    ) -> Optional[UserLocationAccess]:
        """Get the access record for a specific user and location"""
        return (
            self.db.query(UserLocationAccess)
            .filter(
                and_(
                    UserLocationAccess.user_id == user_id,
                    UserLocationAccess.location_id == location_id,
                    UserLocationAccess.is_active == True,
                )
            )
            .first()
        )

    def get_user_accessible_locations(
        self, user_id: str, min_access_level: AccessLevel = AccessLevel.VIEWER
    ) -> List[UserLocationAccess]:
        """Get all locations accessible to a user with minimum access level"""
        return (
            self.db.query(UserLocationAccess)
            .filter(
                and_(
                    UserLocationAccess.user_id == user_id,
                    UserLocationAccess.access_level >= min_access_level,
                    UserLocationAccess.is_active == True,
                )
            )
            .all()
        )

    def get_location_users(
        self, location_id: str, min_access_level: AccessLevel = AccessLevel.VIEWER
    ) -> List[UserLocationAccess]:
        """Get all users with access to a location"""
        return (
            self.db.query(UserLocationAccess)
            .filter(
                and_(
                    UserLocationAccess.location_id == location_id,
                    UserLocationAccess.access_level >= min_access_level,
                    UserLocationAccess.is_active == True,
                )
            )
            .all()
        )

    def grant_access(
        self, user_id: str, location_id: str, access_level: AccessLevel, granted_by: str
    ) -> UserLocationAccess:
        """Grant access to a user for a location"""
        # Check if access already exists
        existing_access = self.get_user_access(user_id, location_id)

        if existing_access:
            # Update existing access
            existing_access.access_level = access_level
            existing_access.granted_by = granted_by
            existing_access.is_active = True
            return self.update(existing_access)
        else:
            # Create new access record
            new_access = UserLocationAccess(
                user_id=user_id,
                location_id=location_id,
                access_level=access_level,
                granted_by=granted_by,
            )
            return self.create(new_access)

    def revoke_access(self, user_id: str, location_id: str) -> bool:
        """Revoke a user's access to a location"""
        access_record = self.get_user_access(user_id, location_id)
        if access_record:
            access_record.is_active = False
            self.update(access_record)
            return True
        return False

    def check_access(
        self,
        user_id: str,
        location_id: str,
        min_access_level: AccessLevel = AccessLevel.VIEWER,
    ) -> bool:
        """Check if user has minimum required access to a location"""
        access_record = self.get_user_access(user_id, location_id)
        return (
            access_record is not None
            and access_record.is_valid
            and access_record.access_level >= min_access_level
        )

    def can_manage_location(self, user_id: str, location_id: str) -> bool:
        """Check if user can manage location settings"""
        return self.check_access(user_id, location_id, AccessLevel.OWNER)

    def can_manage_services(self, user_id: str, location_id: str) -> bool:
        """Check if user can manage services in a location"""
        return self.check_access(user_id, location_id, AccessLevel.MANAGER)

    def can_grant_access(self, user_id: str, location_id: str) -> bool:
        """Check if user can grant access to others for a location"""
        return self.check_access(user_id, location_id, AccessLevel.OWNER)
