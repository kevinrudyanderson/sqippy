from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_user_repository, require_admin
from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.roles import UserRole
from app.auth.schemas import (
    StaffCreate,
    StaffLogin,
    TokenResponse,
    UserRegistration,
    UserResponse,
)
from app.auth.service import AuthService
from app.database import get_db
from app.organizations.models import Organization

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login():
    return {"message": "Login successful"}


@router.post("/staff/login", response_model=TokenResponse)
async def staff_login(
    login_data: StaffLogin,
    response: Response,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    auth_service = AuthService(user_repo, db)
    token_response, refresh_token = auth_service.authenticate_staff(
        login_data.email, login_data.password
    )

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=auth_service.refresh_token_expire_days
        * 24
        * 60
        * 60,  # Convert days to seconds
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="strict",
    )

    return token_response


@router.post("/register", response_model=UserResponse)
def register_user(
    registration_data: UserRegistration,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Register a new business owner - creates organization and user"""
    # Check if user already exists
    existing_user = user_repo.get_by_email(registration_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    auth_service = AuthService(user_repo, db)

    # Create organization first
    organization = Organization(
        name=registration_data.business_name or f"{registration_data.name}'s Business",
        business_type=registration_data.business_type,
    )
    db.add(organization)
    db.flush()  # Get the organization_id without committing

    # Create user as ADMIN of the organization
    user_data = User(
        organization_id=organization.organization_id,
        name=registration_data.name,
        email=registration_data.email,
        phone_number=registration_data.phone_number,
        password=auth_service.hash_password(registration_data.password),
        role=UserRole.ADMIN,  # Business owner starts as admin
        is_active=True,
    )

    user = user_repo.create(user_data)
    return UserResponse.model_validate(user)


@router.post("/staff/create", response_model=UserResponse)
async def create_staff_user(
    staff_data: StaffCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Create a new staff user (admin only)"""
    auth_service = AuthService(user_repo, db)
    user = auth_service.create_staff_user(staff_data)
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Refresh access token using refresh token from HTTP-only cookie"""
    auth_service = AuthService(user_repo, db)

    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    user = auth_service.get_user_from_refresh_token(refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Generate new tokens
    new_access_token = auth_service.create_access_token(user)
    new_refresh_token = auth_service.create_refresh_token(user)

    # Invalidate old refresh token
    auth_service.invalidate_refresh_token(refresh_token)

    # Set new refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=auth_service.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return TokenResponse(
        access_token=new_access_token,
        expires_in=auth_service.access_token_expire_minutes,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Logout by invalidating refresh token from HTTP-only cookie"""
    auth_service = AuthService(user_repo, db)

    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        auth_service.invalidate_refresh_token(refresh_token)

    # Clear the refresh token cookie
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="strict"
    )

    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all_devices(
    response: Response,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """Logout from all devices by invalidating all refresh tokens"""
    auth_service = AuthService(user_repo, db)

    count = auth_service.invalidate_all_user_refresh_tokens(current_user.user_id)

    # Clear the refresh token cookie from current device
    response.delete_cookie(
        key="refresh_token", httponly=True, secure=True, samesite="strict"
    )

    return {"message": f"Logged out from {count} devices"}
