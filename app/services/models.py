import uuid

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)

    # Service details
    category = Column(String)  # e.g., "restaurant", "medical", "retail", etc.
    duration_minutes = Column(Integer)  # Average service duration
    price = Column(Float)  # Optional price field

    # Availability
    is_active = Column(Boolean, default=True)
    max_daily_capacity = Column(Integer)  # Maximum number of customers per day

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    queues = relationship(
        "Queue", back_populates="service", cascade="all, delete-orphan"
    )
