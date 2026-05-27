from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User
from src.api.dependencies import get_current_active_user
from src.services.stripe_service import StripeService
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()


class CheckoutRequest(BaseModel):
    """Schema for creating checkout session."""

    plan: str
    success_url: str
    cancel_url: str


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""

    plan: str
    status: str
    current_period_start: str = None
    current_period_end: str = None

    class Config:
        from_attributes = True


@router.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    return {"plans": StripeService.PLANS}


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's subscription."""
    if not current_user.subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found",
        )

    return {
        "plan": current_user.subscription.plan,
        "status": current_user.subscription.status,
        "current_period_start": current_user.subscription.current_period_start.isoformat() if current_user.subscription.current_period_start else None,
        "current_period_end": current_user.subscription.current_period_end.isoformat() if current_user.subscription.current_period_end else None,
    }


@router.post("/checkout")
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Create a Stripe checkout session."""
    try:
        session = StripeService.create_checkout_session(
            user=current_user,
            plan=checkout_data.plan,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Cancel current subscription."""
    result = StripeService.cancel_subscription(current_user, db)

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return {"message": "Subscription canceled successfully"}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    result = StripeService.handle_webhook(payload, sig_header, db)

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
        )

    return {"status": "success"}


@router.get("/usage-limits")
async def get_usage_limits(
    current_user: User = Depends(get_current_active_user),
):
    """Get usage limits for current user's plan."""
    plan = current_user.subscription.plan if current_user.subscription else "free"
    limits = StripeService.get_usage_limits(plan)

    return {
        "plan": plan,
        "limits": limits,
    }
