from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.repository import UserRepository
from app.locations.models import Location
from app.locations.repository import LocationRepository
from app.locations.schemas import AddLocationRequest
from app.notifications.sms_service import SMSService
from app.queue.models import CustomerStatus, Queue, QueueCustomer, QueueStatus
from app.queue.repository import QueueCustomerRepository, QueueRepository
from app.queue.schemas import (
    AddCustomerToQueueRequest,
    QueueCreate,
    QueuePositionResponse,
    QueueResponse,
    QueueStatusResponse,
    QueueUpdate,
    QueueWizardRequest,
    QueueWizardResponse,
)
from app.services.models import Service
from app.services.repository import ServiceRepository
from app.services.schemas import ServiceCreate


class QueueService:
    def __init__(self, db: Session):
        self.db = db
        self.queue_repo = QueueRepository(db)
        self.customer_repo = QueueCustomerRepository(db)
        self.location_repo = LocationRepository(db)
        self.service_repo = ServiceRepository(db)
        self.user_repo = UserRepository(db)
        self.sms_service = SMSService(db)

    def create_queue(self, queue_data: QueueCreate) -> Queue:
        # Verify location exists (would need location repository)
        # For now, we'll assume location is valid

        queue = Queue(**queue_data.model_dump())
        return self.queue_repo.create(queue)

    def get_queue(self, queue_id: str) -> Queue:
        queue = self.queue_repo.get(queue_id)
        if not queue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Queue not found"
            )
        return queue

    def update_queue(self, queue_id: str, update_data: QueueUpdate) -> Queue:
        queue = self.get_queue(queue_id)
        return self.queue_repo.update_from_schema(queue, update_data)

    def delete_queue(self, queue_id: str) -> Queue:
        queue = self.get_queue(queue_id)

        # Check if there are active customers
        active_customers = self.customer_repo.get_queue_customers(
            queue_id, status=CustomerStatus.WAITING
        )
        if active_customers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete queue with active customers",
            )

        queue.is_active = False
        return self.queue_repo.update(queue)

    def get_queues_by_location(self, location_id: str) -> List[Queue]:
        return self.queue_repo.get_by_location(location_id)

    def get_queues_by_service(self, service_id: str) -> List[Queue]:
        return self.queue_repo.get_by_service(service_id)

    def get_queue_customer(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        return self.customer_repo.get(queue_customer_id)

    async def add_customer_to_queue(
        self, queue_id: str, customer_data: AddCustomerToQueueRequest
    ) -> QueueCustomer:
        # Verify queue exists and is active
        queue = self.get_queue(queue_id)
        if queue.status != QueueStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Queue is not accepting new customers",
            )

        # Check if queue is at capacity
        if queue.max_capacity:
            current_size = len(self.customer_repo.get_waiting_customers(queue_id))
            if current_size >= queue.max_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Queue is at maximum capacity",
                )

        # Validate customer data
        if not customer_data.user_id and not customer_data.customer_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either user_id or customer_name must be provided",
            )

        # Create customer entry
        customer = QueueCustomer(queue_id=queue_id, **customer_data.model_dump())
        customer = self.customer_repo.add_customer_to_queue(customer)

        # Send welcome SMS if phone number is provided
        if customer.customer_phone:
            # Get organization ID
            from app.locations.models import Location
            from app.services.models import Service

            organization_id = (
                self.db.query(Location.organization_id)
                .join(Queue, Queue.location_id == Location.location_id)
                .filter(Queue.queue_id == queue_id)
                .scalar()
            )

            if organization_id:
                position = self.customer_repo.get_customer_position(
                    customer.queue_customer_id
                )
                estimated_wait_time = None
                if queue.estimated_service_time and position and position > 0:
                    estimated_wait_time = queue.estimated_service_time * (position - 1)
                    estimated_wait = f"{estimated_wait_time} minutes"
                else:
                    estimated_wait = "Unknown"

                # Send SMS notification
                sms_success, sms_message = (
                    await self.sms_service.send_queue_notification_sms(
                        organization_id,
                        customer.customer_phone,
                        customer.customer_name or "Customer",
                        queue.name,
                        "queue_subscription",
                        position=position,
                        estimated_wait=estimated_wait,
                    )
                )

                if not sms_success:
                    print(f"Failed to send welcome SMS: {sms_message}")
                    # raise HTTPException(
                    #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    #     detail=f"Failed to send welcome SMS: {sms_message}",
                    # )

        return customer

    def get_queue_status(self, queue_id: str) -> QueueStatusResponse:
        queue = self.get_queue(queue_id)

        waiting_customers = self.customer_repo.get_waiting_customers(queue_id)
        in_service_customers = self.customer_repo.get_queue_customers(
            queue_id, CustomerStatus.IN_SERVICE
        )

        # Calculate average wait time based on recent completions
        # This is a simplified implementation
        average_wait_time = None
        if queue.estimated_service_time and waiting_customers:
            average_wait_time = queue.estimated_service_time * len(waiting_customers)

        return QueueStatusResponse(
            queue_id=queue.queue_id,
            name=queue.name,
            status=queue.status,
            current_size=len(waiting_customers) + len(in_service_customers),
            waiting_customers=len(waiting_customers),
            average_wait_time=average_wait_time,
            is_accepting_customers=(queue.status == QueueStatus.ACTIVE),
        )

    def get_customer_position(self, queue_customer_id: str) -> QueuePositionResponse:
        customer = self.customer_repo.get(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in queue",
            )

        queue = self.queue_repo.get(customer.queue_id)

        # Handle different customer statuses
        if customer.status == CustomerStatus.WAITING:
            position = self.customer_repo.get_customer_position(queue_customer_id)
            ahead_in_queue = position - 1 if position else 0
            estimated_wait_time = None
            if queue.estimated_service_time and position and position > 0:
                estimated_wait_time = queue.estimated_service_time * (position - 1)
            status_message = (
                f"You are #{position} in line. {ahead_in_queue} people ahead of you."
            )
        elif customer.status == CustomerStatus.IN_SERVICE:
            position = None
            ahead_in_queue = None
            estimated_wait_time = 0
            status_message = "You have been called! It's your turn - please proceed to the service area."
        elif customer.status == CustomerStatus.COMPLETED:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = "Your service has been completed. Thank you!"
        elif customer.status == CustomerStatus.CANCELLED:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = "Your queue entry has been cancelled."
        elif customer.status == CustomerStatus.NO_SHOW:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = "You were called but did not respond. Your queue entry has been marked as no-show."
        else:
            position = None
            ahead_in_queue = None
            estimated_wait_time = None
            status_message = f"Your current status: {customer.status.value}"

        # Get customer info from registered user if available
        customer_name = customer.customer_name
        customer_email = customer.customer_email
        customer_phone = customer.customer_phone

        # If customer is a registered user, use their profile info as fallback
        if customer.user_id and customer.user:
            customer_name = customer_name or customer.user.name
            customer_email = customer_email or customer.user.email
            customer_phone = customer_phone or customer.user.phone_number

        return QueuePositionResponse(
            queue_customer_id=queue_customer_id,
            position=position,
            ahead_in_queue=ahead_in_queue,
            estimated_wait_time=estimated_wait_time,
            status=customer.status.value,
            status_message=status_message,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            party_size=customer.party_size,
            queue_name=queue.name,
            queue_id=queue.queue_id,
        )

    async def call_next_customer(self, queue_id: str) -> Optional[QueueCustomer]:
        # queue = self.get_queue(queue_id)
        return await self.customer_repo.call_next_customer(queue_id)

    def complete_customer(self, queue_customer_id: str) -> QueueCustomer:
        customer = self.customer_repo.complete_customer(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found or not in service",
            )
        return customer

    def cancel_customer(self, queue_customer_id: str) -> QueueCustomer:
        customer = self.customer_repo.cancel_customer(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found or cannot be cancelled",
            )
        return customer

    def get_queue_customers(
        self, queue_id: str, status: Optional[CustomerStatus] = None
    ) -> List[QueueCustomer]:
        self.get_queue(queue_id)  # Verify queue exists
        return self.customer_repo.get_queue_customers(queue_id, status)

    def get_user_accessible_queues(self, user_id: str) -> List[Queue]:
        """Get all active queues in the user's organization"""
        return self.queue_repo.get_organization_queues(user_id)

    def get_sms_quota_status(self, organization_id: str) -> dict:
        """Get SMS quota status for organization"""
        return self.sms_service.get_sms_quota_status(organization_id)

    def create_queue_wizard(
        self, wizard_data: QueueWizardRequest, user_id: str
    ) -> QueueWizardResponse:
        """Create queue, service, and location in one operation (wizard)"""
        created_new_location = False
        created_new_service = False

        # Get user's organization
        user = self.user_repo.get(user_id)
        if not user or not user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to an organization to create queues",
            )

        try:
            # Handle location
            if wizard_data.location.useExisting:
                if not wizard_data.location.existingLocationId:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Existing location ID is required when useExisting is true",
                    )
                location = self.location_repo.get(
                    wizard_data.location.existingLocationId
                )
                if not location:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Existing location not found",
                    )
            else:
                if not wizard_data.location.newLocation:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="New location data is required when useExisting is false",
                    )
                # Create new location
                location = Location(
                    organization_id=user.organization_id,
                    **wizard_data.location.newLocation.model_dump(),
                )
                location = self.location_repo.create(location)
                created_new_location = True

            # Handle service
            if wizard_data.service.useExisting:
                if not wizard_data.service.existingServiceId:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Existing service ID is required when useExisting is true",
                    )
                service = self.service_repo.get(wizard_data.service.existingServiceId)
                if not service:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Existing service not found",
                    )
            else:
                if not wizard_data.service.newService:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="New service data is required when useExisting is false",
                    )
                # Create new service (services are now global, no location_id needed)
                service = Service(
                    **wizard_data.service.newService.model_dump(),
                )
                service = self.service_repo.create(service)
                created_new_service = True

            # Create queue
            queue = Queue(
                service_id=service.service_id,
                location_id=location.location_id,
                name=wizard_data.queue.name,
                description=wizard_data.queue.description,
                max_capacity=wizard_data.queue.max_capacity,
                estimated_service_time=wizard_data.queue.estimated_service_time,
            )
            queue = self.queue_repo.create(queue)

            # Commit the transaction
            self.db.commit()

            return QueueWizardResponse(
                queue_id=queue.queue_id,
                queue_name=queue.name,
                service_id=service.service_id,
                service_name=service.name,
                location_id=location.location_id,
                location_name=location.name,
                created_new_service=created_new_service,
                created_new_location=created_new_location,
            )
        except Exception as e:
            # Rollback on any error
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create queue wizard: {str(e)}",
            )

    # Event-based queue methods
    def get_queues_by_event(self, event_name: str) -> List[Queue]:
        """Get all queues for a specific event"""
        return self.queue_repo.get_by_event(event_name)

    def get_mobile_queues(self) -> List[Queue]:
        """Get all mobile/event-based queues"""
        return self.queue_repo.get_mobile_queues()

    def get_queues_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Queue]:
        """Get queues active within a date range"""
        return self.queue_repo.get_queues_by_date_range(start_date, end_date)

    def create_event_queue(
        self,
        service_id: str,
        location_id: str,
        event_name: str,
        event_start_date: datetime,
        event_end_date: datetime,
        queue_name: Optional[str] = None,
        description: Optional[str] = None,
        max_capacity: Optional[int] = None,
        estimated_service_time: Optional[int] = None,
    ) -> Queue:
        """Create a queue for a specific event"""
        # Verify service and location exist
        service = self.service_repo.get(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
            )

        location = self.location_repo.get(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Location not found"
            )

        queue_data = QueueCreate(
            name=queue_name or f"{event_name} - {service.name}",
            description=description or f"Queue for {event_name} at {location.name}",
            service_id=service_id,
            location_id=location_id,
            event_name=event_name,
            event_start_date=event_start_date,
            event_end_date=event_end_date,
            is_mobile_queue=True,
            max_capacity=max_capacity,
            estimated_service_time=estimated_service_time,
        )

        return self.create_queue(queue_data)
