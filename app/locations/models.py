from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, String
from sqlalchemy.orm import relationship

from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    # TODO: Remove this once we use postgres
    # location_id = Column(UUID, primary_key=True, default=uuid4)
    location_id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    province = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True, default="NL")

    is_active = Column(Boolean, default=True)

    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    queues = relationship("Queue", back_populates="location")
