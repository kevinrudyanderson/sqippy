from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.database import get_db
from app.subscriptions.dependencies import get_subscription_service
from app.subscriptions.permissions import require_organization_admin, require_super_admin
from app.subscriptions.schemas import (
    PlanLimits,
    SubscriptionResponse,
    UpgradePlanRequest,
    UsageStats,
    UsageTrackingResponse
)
from app.subscriptions.service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """Get current organization's subscription details"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    subscription = service.get_organization_subscription(current_user.organization_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    response = SubscriptionResponse.from_orm(subscription)
    response.sms_credits_remaining = max(0, subscription.sms_credits_total - subscription.sms_credits_used)
    
    return response


@router.get("/usage", response_model=UsageStats)
async def get_usage_statistics(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """Get current month's usage statistics"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    return service.get_usage_stats(current_user.organization_id)


@router.get("/limits", response_model=PlanLimits)
async def get_plan_limits(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """Get current plan limits and remaining resources"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    return service.get_plan_limits_for_organization(current_user.organization_id)


@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    request: UpgradePlanRequest,
    current_user: Annotated[User, Depends(require_organization_admin)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """Upgrade organization's subscription plan"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    subscription = service.upgrade_plan(current_user.organization_id, request.new_plan)
    
    response = SubscriptionResponse.from_orm(subscription)
    response.sms_credits_remaining = max(0, subscription.sms_credits_total - subscription.sms_credits_used)
    
    return response


@router.post("/cancel")
async def cancel_subscription(
    current_user: Annotated[User, Depends(require_organization_admin)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """Cancel organization's subscription (reverts to FREE plan)"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    success = service.cancel_subscription(current_user.organization_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel subscription"
        )
    
    return {"message": "Subscription cancelled successfully, reverted to FREE plan"}


@router.get("/history")
async def get_usage_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Get historical usage data for the organization"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    from app.subscriptions.repository import UsageTrackingRepository
    
    usage_repo = UsageTrackingRepository(db)
    history = usage_repo.get_organization_history(current_user.organization_id, limit=12)
    
    return [UsageTrackingResponse.from_orm(usage) for usage in history]


@router.post("/check-feature/{feature}")
async def check_feature_access(
    feature: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """Check if organization has access to a specific feature"""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )
    
    has_access = service.check_feature_access(current_user.organization_id, feature)
    
    return {
        "feature": feature,
        "has_access": has_access
    }


# Admin endpoints for super admins
@router.get("/admin/{organization_id}", response_model=SubscriptionResponse)
async def get_organization_subscription(
    organization_id: str,
    current_user: Annotated[User, Depends(require_super_admin)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """[Admin] Get any organization's subscription details"""
    subscription = service.get_organization_subscription(organization_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    response = SubscriptionResponse.from_orm(subscription)
    response.sms_credits_remaining = max(0, subscription.sms_credits_total - subscription.sms_credits_used)
    
    return response


@router.post("/admin/{organization_id}/upgrade")
async def admin_upgrade_subscription(
    organization_id: str,
    request: UpgradePlanRequest,
    current_user: Annotated[User, Depends(require_super_admin)],
    service: Annotated[SubscriptionService, Depends(get_subscription_service)]
):
    """[Admin] Upgrade any organization's subscription"""
    # Admin can bypass payment requirements
    subscription = service.upgrade_plan(organization_id, request.new_plan, bypass_payment=True)
    
    response = SubscriptionResponse.from_orm(subscription)
    response.sms_credits_remaining = max(0, subscription.sms_credits_total - subscription.sms_credits_used)
    
    return response