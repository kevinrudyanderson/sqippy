from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user, require_authenticated_user, require_staff_or_admin, get_user_repository
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.schemas import CustomerSignUp
from app.queue.dependencies import get_queue_service
from app.queue.models import CustomerStatus
from app.queue.schemas import (
    AddCustomerToQueueRequest,
    QueueCreate,
    QueueCustomerResponse,
    QueuePositionResponse,
    QueueResponse,
    QueueStatusResponse,
    QueueUpdate,
    QueueWizardRequest,
    QueueWizardResponse,
)
from app.queue.service import QueueService

router = APIRouter(prefix="/queues", tags=["queues"])


# Queue Management Endpoints
@router.post("/", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue(
    queue_data: QueueCreate,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Create a new queue (Staff/Admin only)"""
    queue = queue_service.create_queue(queue_data)
    return QueueResponse(**queue.__dict__, current_size=0, waiting_customers=0)


@router.post("/wizard", response_model=QueueWizardResponse, status_code=status.HTTP_201_CREATED)
async def create_queue_wizard(
    wizard_data: QueueWizardRequest,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Create queue, service, and location in one operation (Wizard endpoint)"""
    return queue_service.create_queue_wizard(wizard_data, current_user.user_id)


@router.get("/{queue_id}", response_model=QueueResponse)
async def get_queue(
    queue_id: str, queue_service: QueueService = Depends(get_queue_service)
):
    """Get queue details (public endpoint)"""
    queue = queue_service.get_queue(queue_id)
    # Get customer counts
    waiting_customers = queue_service.customer_repo.get_waiting_customers(queue_id)
    in_service_customers = queue_service.customer_repo.get_queue_customers(
        queue_id, CustomerStatus.IN_SERVICE
    )

    return QueueResponse(
        **queue.__dict__,
        current_size=len(waiting_customers) + len(in_service_customers),
        waiting_customers=len(waiting_customers)
    )


@router.patch("/{queue_id}", response_model=QueueResponse)
async def update_queue(
    queue_id: str,
    update_data: QueueUpdate,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Update queue settings (Staff/Admin only)"""
    queue = queue_service.update_queue(queue_id, update_data)
    # Get customer counts
    waiting_customers = queue_service.customer_repo.get_waiting_customers(queue_id)
    in_service_customers = queue_service.customer_repo.get_queue_customers(
        queue_id, CustomerStatus.IN_SERVICE
    )

    return QueueResponse(
        **queue.__dict__,
        current_size=len(waiting_customers) + len(in_service_customers),
        waiting_customers=len(waiting_customers)
    )


@router.delete("/{queue_id}", response_model=QueueResponse)
async def delete_queue(
    queue_id: str,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Deactivate a queue (Staff/Admin only)"""
    queue = queue_service.delete_queue(queue_id)
    return QueueResponse(**queue.__dict__, current_size=0, waiting_customers=0)


@router.get("/location/{location_id}", response_model=List[QueueResponse])
async def get_queues_by_location(
    location_id: str, queue_service: QueueService = Depends(get_queue_service)
):
    """Get all queues for a location (public endpoint)"""
    queues = queue_service.get_queues_by_location(location_id)
    response = []
    for queue in queues:
        waiting_customers = queue_service.customer_repo.get_waiting_customers(
            queue.queue_id
        )
        in_service_customers = queue_service.customer_repo.get_queue_customers(
            queue.queue_id, CustomerStatus.IN_SERVICE
        )
        response.append(
            QueueResponse(
                **queue.__dict__,
                current_size=len(waiting_customers) + len(in_service_customers),
                waiting_customers=len(waiting_customers)
            )
        )
    return response


@router.get("/service/{service_id}", response_model=List[QueueResponse])
async def get_queues_by_service(
    service_id: str, queue_service: QueueService = Depends(get_queue_service)
):
    """Get all queues for a service (public endpoint)"""
    queues = queue_service.get_queues_by_service(service_id)
    response = []
    for queue in queues:
        waiting_customers = queue_service.customer_repo.get_waiting_customers(
            queue.queue_id
        )
        in_service_customers = queue_service.customer_repo.get_queue_customers(
            queue.queue_id, CustomerStatus.IN_SERVICE
        )
        response.append(
            QueueResponse(
                **queue.__dict__,
                current_size=len(waiting_customers) + len(in_service_customers),
                waiting_customers=len(waiting_customers)
            )
        )
    return response


@router.get("/user/queues", response_model=List[QueueResponse])
async def get_user_queues(
    current_user: User = Depends(require_authenticated_user),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Get all queues accessible to the logged in user"""
    queues = queue_service.get_user_accessible_queues(current_user.user_id)
    response = []
    for queue in queues:
        waiting_customers = queue_service.customer_repo.get_waiting_customers(
            queue.queue_id
        )
        in_service_customers = queue_service.customer_repo.get_queue_customers(
            queue.queue_id, CustomerStatus.IN_SERVICE
        )
        response.append(
            QueueResponse(
                **queue.__dict__,
                current_size=len(waiting_customers) + len(in_service_customers),
                waiting_customers=len(waiting_customers)
            )
        )
    return response


# Customer Management Endpoints
@router.post(
    "/{queue_id}/customers",
    response_model=QueueCustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_customer_to_queue(
    queue_id: str,
    customer_data: AddCustomerToQueueRequest,
    current_user: Optional[User] = Depends(get_current_user),
    queue_service: QueueService = Depends(get_queue_service),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Add a customer to the queue (public endpoint - no authentication required)"""
    # If user is logged in, use their ID
    if current_user and not customer_data.user_id:
        customer_data.user_id = current_user.user_id
    elif not current_user and not customer_data.user_id:
        # Create customer account if email or phone is provided
        if customer_data.customer_email or customer_data.customer_phone:
            customer_signup = CustomerSignUp(
                name=customer_data.customer_name,
                email=customer_data.customer_email,
                phone_number=customer_data.customer_phone
            )
            user = user_repo.get_or_create_customer(customer_signup)
            customer_data.user_id = user.user_id

    customer = queue_service.add_customer_to_queue(queue_id, customer_data)

    # Calculate estimated wait time
    queue = queue_service.get_queue(queue_id)
    position = queue_service.customer_repo.get_customer_position(
        customer.queue_customer_id
    )
    estimated_wait_time = None
    if queue.estimated_service_time and position and position > 0:
        estimated_wait_time = queue.estimated_service_time * (position - 1)

    return QueueCustomerResponse(
        **customer.__dict__, position=position, estimated_wait_time=estimated_wait_time
    )


@router.get("/{queue_id}/status", response_model=QueueStatusResponse)
async def get_queue_status(
    queue_id: str, queue_service: QueueService = Depends(get_queue_service)
):
    """Get current queue status and statistics (public endpoint)"""
    return queue_service.get_queue_status(queue_id)


@router.get("/{queue_id}/customers", response_model=List[QueueCustomerResponse])
async def get_queue_customers(
    queue_id: str,
    status: Optional[CustomerStatus] = None,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Get all customers in a queue (Staff/Admin only)"""
    customers = queue_service.get_queue_customers(queue_id, status)
    queue = queue_service.get_queue(queue_id)

    response = []
    for customer in customers:
        position = queue_service.customer_repo.get_customer_position(
            customer.queue_customer_id
        )
        estimated_wait_time = None
        if queue.estimated_service_time and position and position > 0:
            estimated_wait_time = queue.estimated_service_time * (position - 1)

        response.append(
            QueueCustomerResponse(
                **customer.__dict__,
                position=position,
                estimated_wait_time=estimated_wait_time
            )
        )

    return response


@router.get(
    "/customers/{queue_customer_id}/position", response_model=QueuePositionResponse
)
async def get_customer_position(
    queue_customer_id: str, queue_service: QueueService = Depends(get_queue_service)
):
    """Get a customer's current position in the queue (public endpoint)"""
    return queue_service.get_customer_position(queue_customer_id)


@router.post("/{queue_id}/call-next", response_model=Optional[QueueCustomerResponse])
async def call_next_customer(
    queue_id: str,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Call the next customer in the queue (Staff/Admin only)"""
    customer = queue_service.call_next_customer(queue_id)
    if not customer:
        return None

    return QueueCustomerResponse(
        **customer.__dict__, position=None, estimated_wait_time=0
    )


@router.patch(
    "/customers/{queue_customer_id}/complete", response_model=QueueCustomerResponse
)
async def complete_customer(
    queue_customer_id: str,
    current_user: User = Depends(require_staff_or_admin),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Mark a customer as completed (Staff/Admin only)"""
    customer = queue_service.complete_customer(queue_customer_id)
    return QueueCustomerResponse(
        **customer.__dict__, position=None, estimated_wait_time=0
    )


@router.patch(
    "/customers/{queue_customer_id}/cancel", response_model=QueueCustomerResponse
)
async def cancel_customer(
    queue_customer_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    queue_service: QueueService = Depends(get_queue_service),
):
    """Cancel a customer from the queue"""
    # Allow customers to cancel their own entry or staff/admin to cancel any
    if current_user:
        # If logged in, check if it's their own entry or they're staff/admin
        customer = queue_service.get_queue_customer(queue_customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
            )
        
        # Allow if it's their own entry or they're staff/admin
        if (customer.user_id != current_user.user_id and 
            current_user.role not in ["staff", "admin", "super_admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
    # If not logged in, this is likely a public cancellation which we'll allow for now
    # In production, you might want to require a phone number or other verification

    customer = queue_service.cancel_customer(queue_customer_id)
    return QueueCustomerResponse(
        **customer.__dict__, position=None, estimated_wait_time=0
    )
