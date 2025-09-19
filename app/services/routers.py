from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.roles import UserRole
from app.database import get_db
from app.locations.repository import LocationRepository
from app.organizations.dependencies import require_organization_member
from app.services.repository import ServiceRepository
from app.services.schemas import Service as ServiceResponse
from app.services.schemas import ServiceCreate, ServiceUpdate, ServiceWithQueues
from app.services.service import ServiceService

router = APIRouter(prefix="/services", tags=["services"])


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    service_data: ServiceCreate,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Create a new service (services are now global, not tied to specific locations)."""

    service_service = ServiceService(db)
    return service_service.create_service(service_data)


@router.get("/", response_model=List[ServiceResponse])
def get_all_services(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Get all services for the user's organization."""
    service_repository = ServiceRepository(db)

    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all services
        return service_repository.get_active_services()[skip : skip + limit]
    else:
        # Regular users see all services in their organization
        return service_repository.get_by_organization(
            current_user.organization_id, skip, limit
        )


@router.get("/location/{location_id}", response_model=List[ServiceResponse])
def get_services_by_location(
    location_id: str,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Get all services (services are now global, not tied to specific locations)."""
    service_repository = ServiceRepository(db)

    # Since services are now global, return all active services
    # The location_id parameter is kept for backward compatibility
    return service_repository.get_active_services()


@router.get("/category/{category}", response_model=List[ServiceResponse])
def get_services_by_category(
    category: str,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Get all services by category for the user's organization."""
    service_repository = ServiceRepository(db)

    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all services
        return service_repository.get_by_category(category)
    else:
        # Regular users see services in their organization only
        return service_repository.get_by_category_and_organization(
            category, current_user.organization_id
        )


@router.get("/{service_id}", response_model=ServiceWithQueues)
def get_service(
    service_id: str,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Get a specific service with its queues if user has access."""
    service_repository = ServiceRepository(db)

    if current_user.role == UserRole.SUPER_ADMIN:
        service = service_repository.get(service_id)
    else:
        # Get service and verify it belongs to user's organization
        service = service_repository.get_by_organization_and_id(
            service_id, current_user.organization_id
        )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or access denied",
        )
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: str,
    service_update: ServiceUpdate,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Update a service if it belongs to user's organization."""
    service_service = ServiceService(db)

    # Verify service belongs to user's organization
    if current_user.role != UserRole.SUPER_ADMIN:
        service_repo = ServiceRepository(db)
        service = service_repo.get_by_organization_and_id(
            service_id, current_user.organization_id
        )
        if not service:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this service",
            )

    updated_service = service_service.update_service(service_id, service_update)
    if not updated_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return updated_service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: str,
    current_user=Depends(require_organization_member),
    db: Session = Depends(get_db),
):
    """Delete a service (soft delete by setting is_active=False) if it belongs to user's organization."""
    service_service = ServiceService(db)

    # Verify service belongs to user's organization
    if current_user.role != UserRole.SUPER_ADMIN:
        service_repo = ServiceRepository(db)
        service = service_repo.get_by_organization_and_id(
            service_id, current_user.organization_id
        )
        if not service:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this service",
            )

    if not service_service.delete_service(service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return
