from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import inspect

T = TypeVar("T")  # generic type so we can use any class that inherits from BaseModel


class BaseRepository(ABC, Generic[T]):
    """
    Base class for all repositories.
    """

    def __init__(self, db: Session, model_class: Type[T]):
        self.db = db
        self.model_class = model_class  # concrete class

    def get_by_id(self, id: UUID) -> T:
        # Use SQLAlchemy inspection to get the primary key column
        mapper = inspect(self.model_class)
        pk_column = mapper.primary_key[0]  # Get the first primary key column
        return self.db.query(self.model_class).filter(pk_column == str(id)).first()

    def get(self, id: str) -> Optional[T]:
        """Get by ID accepting string format (for compatibility with string UUIDs)"""
        mapper = inspect(self.model_class)
        pk_column = mapper.primary_key[0]
        return self.db.query(self.model_class).filter(pk_column == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return self.db.query(self.model_class).offset(skip).limit(limit).all()

    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: T) -> T:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update_from_schema(self, obj: T, update_schema: BaseModel) -> T:
        """
        Update an object from a Pydantic schema, only setting fields that are not None.
        IMPORTANT: Only updates fields that are explicitly defined in the schema.
        """
        update_data = update_schema.model_dump(exclude_unset=True)
        
        # Get the fields defined in the schema model
        schema_fields = set(update_schema.__class__.model_fields.keys())
        
        for field, value in update_data.items():
            # Only update if field is defined in the schema AND exists on the object
            if field in schema_fields and hasattr(obj, field):
                setattr(obj, field, value)
        return self.update(obj)

    def delete(self, obj: T) -> T:
        self.db.delete(obj)
        self.db.commit()
        return obj

    def check_user_access(self, user_id: str, resource_id: str, min_access_level=None) -> bool:
        """
        Check if user has access to a resource. Override in specific repositories.
        This is a default implementation that should be overridden by location-based repositories.
        """
        return False

    def get_accessible_resources(self, user_id: str, min_access_level=None, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get resources accessible to a user. Override in specific repositories.
        This is a default implementation that should be overridden by location-based repositories.
        """
        return []

    def get_accessible_resource(self, user_id: str, resource_id: str, min_access_level=None) -> Optional[T]:
        """
        Get a specific resource if user has access to it. Override in specific repositories.
        This is a default implementation that should be overridden by location-based repositories.
        """
        return None
