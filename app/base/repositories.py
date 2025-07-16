from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

T = TypeVar("T")  # generic type so we can use any class that inherits from BaseModel


class BaseRepository(ABC, Generic[T]):
    """
    Base class for all repositories.
    """

    def __init__(self, db: Session, model_class: Type[T]):
        self.db = db
        self.model_class = model_class  # concrete class

    def get_by_id(self, id: UUID) -> T:
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()

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
        """
        update_data = update_schema.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        return self.update(obj)

    def delete(self, obj: T) -> T:
        self.db.delete(obj)
        self.db.commit()
        return obj
