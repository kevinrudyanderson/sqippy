from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.access.models import AccessLevel, UserLocationAccess
from app.auth.models import User
from app.base.repositories import BaseRepository
from app.locations.models import Location
from app.notifications.service import notification_service
from app.organizations.models import Organization
from app.queue.models import CustomerStatus, Queue, QueueCustomer, QueueStatus
from app.services.models import Service
from app.subscriptions.service import SubscriptionService


class QueueRepository(BaseRepository[Queue]):
    def __init__(self, db: Session):
        super().__init__(db, Queue)

    def get_by_service(self, service_id: str) -> List[Queue]:
        return (
            self.db.query(Queue)
            .filter(Queue.service_id == service_id, Queue.is_active == True)
            .all()
        )

    def get_by_location(self, location_id: str) -> List[Queue]:
        """Get all queues for a location"""
        return (
            self.db.query(Queue)
            .filter(Queue.location_id == location_id, Queue.is_active == True)
            .all()
        )

    def get_active_queues(self) -> List[Queue]:
        return (
            self.db.query(Queue)
            .filter(Queue.status == QueueStatus.ACTIVE, Queue.is_active == True)
            .all()
        )

    # Access-based methods (inherit access from service's location)
    def check_user_access(
        self,
        user_id: str,
        queue_id: str,
        min_access_level: AccessLevel = AccessLevel.VIEWER,
    ) -> bool:
        """Check if user has access to a queue through its service's location"""
        return (
            self.db.query(Queue)
            .join(Service, Queue.service_id == Service.service_id)
            .join(
                UserLocationAccess,
                Queue.location_id == UserLocationAccess.location_id,
            )
            .filter(
                and_(
                    Queue.queue_id == queue_id,
                    UserLocationAccess.user_id == user_id,
                    UserLocationAccess.access_level >= min_access_level,
                    UserLocationAccess.is_active == True,
                )
            )
            .first()
            is not None
        )

    def get_accessible_resources(
        self,
        user_id: str,
        min_access_level: AccessLevel = AccessLevel.VIEWER,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Queue]:
        """Get queues accessible to a user through their location access"""
        return (
            self.db.query(Queue)
            .join(Service, Queue.service_id == Service.service_id)
            .join(
                UserLocationAccess,
                Queue.location_id == UserLocationAccess.location_id,
            )
            .filter(
                and_(
                    UserLocationAccess.user_id == user_id,
                    UserLocationAccess.access_level >= min_access_level,
                    UserLocationAccess.is_active == True,
                    Queue.is_active == True,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_accessible_resource(
        self,
        user_id: str,
        queue_id: str,
        min_access_level: AccessLevel = AccessLevel.VIEWER,
    ) -> Optional[Queue]:
        """Get a specific queue if user has access to it through its service's location"""
        return (
            self.db.query(Queue)
            .join(Service, Queue.service_id == Service.service_id)
            .join(
                UserLocationAccess,
                Queue.location_id == UserLocationAccess.location_id,
            )
            .filter(
                and_(
                    Queue.queue_id == queue_id,
                    UserLocationAccess.user_id == user_id,
                    UserLocationAccess.access_level >= min_access_level,
                    UserLocationAccess.is_active == True,
                )
            )
            .first()
        )

    def get_organization_queues(self, user_id: str) -> List[Queue]:
        """Get all active queues in the user's organization"""
        return (
            self.db.query(Queue)
            .join(Location, Queue.location_id == Location.location_id)
            .join(
                Organization, Location.organization_id == Organization.organization_id
            )
            .join(User, Organization.organization_id == User.organization_id)
            .filter(
                and_(
                    User.user_id == user_id,
                    Queue.is_active == True,
                    Queue.status == QueueStatus.ACTIVE,
                )
            )
            .all()
        )

    def get_by_event(self, event_name: str) -> List[Queue]:
        """Get all queues for a specific event"""
        return (
            self.db.query(Queue)
            .filter(Queue.event_name == event_name, Queue.is_active == True)
            .all()
        )

    def get_mobile_queues(self) -> List[Queue]:
        """Get all mobile/event-based queues"""
        return (
            self.db.query(Queue)
            .filter(Queue.is_mobile_queue == True, Queue.is_active == True)
            .all()
        )

    def get_queues_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Queue]:
        """Get queues active within a date range"""
        return (
            self.db.query(Queue)
            .filter(
                Queue.event_start_date <= end_date,
                Queue.event_end_date >= start_date,
                Queue.is_active == True,
            )
            .all()
        )


class QueueCustomerRepository(BaseRepository[QueueCustomer]):
    def __init__(self, db: Session):
        super().__init__(db, QueueCustomer)

    def add_customer_to_queue(self, customer: QueueCustomer) -> QueueCustomer:
        # No need to set position - joined_at is automatically set
        return self.create(customer)

    def get_queue_customers(
        self, queue_id: str, status: Optional[CustomerStatus] = None
    ) -> List[QueueCustomer]:
        query = self.db.query(QueueCustomer).filter(QueueCustomer.queue_id == queue_id)

        if status:
            query = query.filter(QueueCustomer.status == status)

        return query.order_by(QueueCustomer.joined_at).all()

    def get_waiting_customers(self, queue_id: str) -> List[QueueCustomer]:
        return self.get_queue_customers(queue_id, CustomerStatus.WAITING)

    def get_customer_position(self, queue_customer_id: str) -> Optional[int]:
        customer = self.get(queue_customer_id)
        if not customer or customer.status != CustomerStatus.WAITING:
            return None

        # Count customers ahead in queue (joined earlier)
        ahead_count = (
            self.db.query(QueueCustomer)
            .filter(
                QueueCustomer.queue_id == customer.queue_id,
                QueueCustomer.status == CustomerStatus.WAITING,
                QueueCustomer.joined_at < customer.joined_at,
            )
            .count()
        )

        return ahead_count + 1

    async def call_next_customer(self, queue_id: str) -> Optional[QueueCustomer]:
        # Get the next waiting customer (earliest joined_at)
        next_customer = (
            self.db.query(QueueCustomer)
            .filter(
                QueueCustomer.queue_id == queue_id,
                QueueCustomer.status == CustomerStatus.WAITING,
            )
            .join(Queue, QueueCustomer.queue_id == Queue.queue_id)
            .order_by(QueueCustomer.joined_at)
            .first()
        )

        if not next_customer:
            return None

        # Get organization ID for quota tracking
        organization_id = (
            self.db.query(Location.organization_id)
            .join(Queue, Queue.location_id == Location.location_id)
            .filter(Queue.queue_id == queue_id)
            .scalar()
        )

        # Initialize subscription service for quota tracking
        subscription_service = SubscriptionService(self.db)

        # Try to send notifications BEFORE changing status
        email_sent = False
        sms_sent = False
        notification_errors = []

        # Try email notification
        if next_customer.customer_email:
            try:
                email_result = await notification_service.send_next_in_line_email(
                    next_customer.customer_email,
                    next_customer.customer_name,
                    next_customer.queue.name,
                    next_customer.queue.location.name,
                )
                if email_result.success:
                    email_sent = True
                    subscription_service.track_email_sent(organization_id)
                else:
                    notification_errors.append(f"Email failed: {email_result.error}")
            except Exception as e:
                notification_errors.append(f"Email failed: {str(e)}")

        # Try SMS notification if phone number is available and organization has SMS credits
        if next_customer.customer_phone and organization_id:
            can_send_sms, sms_message = subscription_service.can_send_sms(
                organization_id
            )

            if can_send_sms:
                try:
                    sms_result = await notification_service.send_next_in_line_sms(
                        next_customer.customer_phone,
                        next_customer.customer_name,
                        next_customer.queue.name,
                        next_customer.queue.location.name,
                    )
                    if sms_result.success:
                        sms_sent = True
                        subscription_service.use_sms_credits(organization_id, 1)
                    else:
                        notification_errors.append(f"SMS failed: {sms_result.error}")
                except Exception as e:
                    notification_errors.append(f"SMS failed: {str(e)}")
            else:
                notification_errors.append(f"Cannot send SMS: {sms_message}")

        # Check if at least one notification was sent successfully
        if not email_sent and not sms_sent:
            # If customer has no contact info, we can't notify them
            if not next_customer.customer_email and not next_customer.customer_phone:
                # Change status anyway - they'll need to check manually
                next_customer.status = CustomerStatus.IN_SERVICE
                next_customer.called_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(next_customer)
                print(
                    f"Customer {next_customer.customer_name} called (no contact info - manual check required)"
                )
            else:
                # We have contact info but all notifications failed - raise exception
                error_message = f"Failed to notify customer {next_customer.customer_name}: {'; '.join(notification_errors)}"
                print(error_message)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message,
                )
        else:
            # At least one notification succeeded - update status
            next_customer.status = CustomerStatus.IN_SERVICE
            next_customer.called_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(next_customer)

            # Log successful notification status
            print(
                f"Customer {next_customer.customer_name} called successfully. Email: {'✓' if email_sent else '✗'}, SMS: {'✓' if sms_sent else '✗'}"
            )

        return next_customer

    async def call_customer_by_id(
        self, queue_customer_id: str
    ) -> Optional[QueueCustomer]:
        customer = self.get(queue_customer_id)
        if not customer or customer.status != CustomerStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer not found or not in waiting status",
            )

        queue_id = customer.queue_id

        # Get organization ID for quota tracking
        organization_id = (
            self.db.query(Location.organization_id)
            .filter(Queue.queue_id == customer.queue_id)
            .join(Queue, Queue.location_id == Location.location_id)
            .scalar()
        )

        # Initialize subscription service for quota tracking
        subscription_service = SubscriptionService(self.db)

        # Try to send notifications BEFORE changing status
        email_sent = False
        sms_sent = False
        notification_errors = []

        # Try email notification
        if customer.customer_email:
            try:
                email_result = await notification_service.send_next_in_line_email(
                    customer.customer_email,
                    customer.customer_name,
                    customer.queue.name,
                    customer.queue.location.name,
                )
                if email_result.success:
                    email_sent = True
                    subscription_service.track_email_sent(organization_id)
                else:
                    notification_errors.append(f"Email failed: {email_result.error}")
            except Exception as e:
                notification_errors.append(f"Email failed: {str(e)}")

        # Try SMS notification if phone number is available and organization has SMS credits
        if customer.customer_phone and organization_id:
            can_send_sms, sms_message = subscription_service.can_send_sms(
                organization_id
            )

            if can_send_sms:
                try:
                    sms_result = await notification_service.send_next_in_line_sms(
                        customer.customer_phone,
                        customer.customer_name,
                        customer.queue.name,
                        customer.queue.location.name,
                    )
                    if sms_result.success:
                        sms_sent = True
                        subscription_service.use_sms_credits(organization_id, 1)
                    else:
                        notification_errors.append(f"SMS failed: {sms_result.error}")
                except Exception as e:
                    notification_errors.append(f"SMS failed: {str(e)}")
            else:
                notification_errors.append(f"Cannot send SMS: {sms_message}")

        # Check if at least one notification was sent successfully
        if not email_sent and not sms_sent:
            # If customer has no contact info, we can't notify them
            if not customer.customer_email and not customer.customer_phone:
                # Change status anyway - they'll need to check manually
                customer.status = CustomerStatus.IN_SERVICE
                customer.called_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(customer)
                print(
                    f"Customer {customer.customer_name} called (no contact info - manual check required)"
                )
            else:
                # We have contact info but all notifications failed - raise exception
                error_message = f"Failed to notify customer {customer.customer_name}: {'; '.join(notification_errors)}"
                print(error_message)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_message,
                )
        else:
            # At least one notification succeeded - update status
            customer.status = CustomerStatus.IN_SERVICE
            customer.called_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(customer)

            # Log successful notification status
            print(
                f"Customer {customer.customer_name} called successfully. Email: {'✓' if email_sent else '✗'}, SMS: {'✓' if sms_sent else '✗'}"
            )

        return customer

    def complete_customer(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        customer = self.get(queue_customer_id)
        if customer and customer.status == CustomerStatus.IN_SERVICE:
            customer.status = CustomerStatus.COMPLETED
            customer.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(customer)
            return customer
        return None

    def cancel_customer(self, queue_customer_id: str) -> Optional[QueueCustomer]:
        customer = self.get(queue_customer_id)
        if customer and customer.status in [
            CustomerStatus.WAITING,
            CustomerStatus.IN_SERVICE,
        ]:
            customer.status = CustomerStatus.CANCELLED
            customer.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(customer)
            return customer
        return None

    # Event-based query methods
