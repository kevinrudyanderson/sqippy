from fastapi import APIRouter, Depends

from app.auth.dependencies import get_user_repository, require_admin
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.schemas import StaffCreate, StaffLogin, TokenResponse, UserResponse
from app.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login():
    return {"message": "Login successful"}


@router.post("/staff/login", response_model=TokenResponse)
async def staff_login(
    login_data: StaffLogin, user_repo: UserRepository = Depends(get_user_repository)
):
    auth_service = AuthService(user_repo)
    return auth_service.authenticate_staff(login_data.email, login_data.password)


@router.post("/staff/create", response_model=UserResponse)
async def create_staff_user(
    staff_data: StaffCreate,
    current_admin: User = Depends(require_admin),
    user_repo: UserRepository = Depends(get_user_repository),
):
    print(current_admin)
    auth_service = AuthService(user_repo)
    user = auth_service.create_staff_user(staff_data)
    return UserResponse.model_validate(user)
