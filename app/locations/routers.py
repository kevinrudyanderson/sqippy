from fastapi import APIRouter, Depends

from app.auth.models import User
from app.locations.dependencies import get_location_service
from app.locations.permissions import require_location_management_permission
from app.locations.schemas import AddLocationRequest, LocationResponse
from app.locations.service import LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/", response_model=LocationResponse)
async def create_location(
    location: AddLocationRequest,
    current_user: User = Depends(require_location_management_permission),
    location_service: LocationService = Depends(get_location_service),
):

    return LocationResponse(**location_service.create(location).__dict__)
