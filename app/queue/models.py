import enum
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class QueueStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class CustomerStatus(enum.Enum):
    WAITING = "waiting"
    IN_SERVICE = "in_service"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Queue(Base):
    __tablename__ = "queues"

    # TODO: Remove this once we use postgres
    # queue_id = Column(UUID, primary_key=True, default=uuid4)
    queue_id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Foreign keys
    service_id = Column(String, ForeignKey("services.service_id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.location_id"), nullable=False)

    status = Column(Enum(QueueStatus), default=QueueStatus.ACTIVE, nullable=False)

    # Event/Mobile queue fields
    event_name = Column(String, nullable=True)  # "Amsterdam Festival", "Utrecht Event"
    event_start_date = Column(DateTime, nullable=True)
    event_end_date = Column(DateTime, nullable=True)
    is_mobile_queue = Column(Boolean, default=False)

    # Queue configuration
    max_capacity = Column(Integer, nullable=True)  # Optional max queue size
    estimated_service_time = Column(
        Integer, nullable=True
    )  # Average service time in minutes

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    service = relationship("Service", back_populates="queues")
    location = relationship("Location", back_populates="queues")
    customers = relationship(
        "QueueCustomer", back_populates="queue", order_by="QueueCustomer.joined_at"
    )


class QueueCustomer(Base):
    __tablename__ = "queue_customers"

    # TODO: Remove this once we use postgres
    # queue_customer_id = Column(UUID, primary_key=True, default=uuid4)
    queue_customer_id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Foreign keys
    queue_id = Column(String, ForeignKey("queues.queue_id"), nullable=False)
    user_id = Column(
        String, ForeignKey("users.user_id"), nullable=True
    )  # Optional, for registered users

    # Customer info (for non-registered customers)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)

    # Queue status
    status = Column(
        Enum(CustomerStatus), default=CustomerStatus.WAITING, nullable=False
    )

    # Timing
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    called_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Additional info
    party_size = Column(Integer, default=1)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    queue = relationship("Queue", back_populates="customers")

    user = relationship("app.auth.models.User", backref="queue_entries")
