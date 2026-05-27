"""
Stripe payment service for subscription management.
"""
import stripe
from typing import Dict, Any, Optional
from datetime import datetime
from src.config import settings
from src.models import User, Subscription
from sqlalchemy.orm import Session

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Handles Stripe payment operations."""

    # Subscription plans
    PLANS = {
        "free": {
            "name": "Free",
            "price": 0,
            "papers_per_day": 10,
            "experiments_per_week": 1,
            "features": ["Basic paper discovery", "Limited experiments", "Community support"],
        },
        "pro": {
            "name": "Pro",
            "price": 29,  # USD per month
            "papers_per_day": 100,
            "experiments_per_week": -1,  # Unlimited
            "features": [
                "Advanced paper discovery",
                "Unlimited experiments",
                "Priority support",
                "API access",
            ],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 99,  # USD per month
            "papers_per_day": -1,  # Unlimited
            "experiments_per_week": -1,  # Unlimited
            "features": [
                "Everything in Pro",
                "Custom limits",
                "Dedicated support",
                "SLA guarantee",
                "Team collaboration",
            ],
        },
    }

    @staticmethod
    def create_customer(user: User) -> str:
        """
        Create a Stripe customer for a user.

        Args:
            user: User object

        Returns:
            str: Stripe customer ID
        """
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name or user.username,
            metadata={"user_id": user.id},
        )
        return customer.id

    @staticmethod
    def create_checkout_session(
        user: User,
        plan: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription.

        Args:
            user: User object
            plan: Plan name (pro or enterprise)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            dict: Checkout session data
        """
        if plan not in ["pro", "enterprise"]:
            raise ValueError("Invalid plan")

        plan_data = StripeService.PLANS[plan]

        # Create or get customer
        if not user.subscription or not user.subscription.stripe_customer_id:
            customer_id = StripeService.create_customer(user)
        else:
            customer_id = user.subscription.stripe_customer_id

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Full-Auto-Research {plan_data['name']}",
                            "description": ", ".join(plan_data["features"]),
                        },
                        "unit_amount": plan_data["price"] * 100,  # Convert to cents
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user.id, "plan": plan},
        )

        return {
            "session_id": session.id,
            "url": session.url,
        }

    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str, db: Session) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            payload: Webhook payload
            sig_header: Stripe signature header
            db: Database session

        Returns:
            dict: Processing result
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except ValueError:
            return {"status": "error", "message": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"status": "error", "message": "Invalid signature"}

        # Handle different event types
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            return StripeService._handle_checkout_completed(session, db)

        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            return StripeService._handle_subscription_updated(subscription, db)

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            return StripeService._handle_subscription_deleted(subscription, db)

        elif event["type"] == "invoice.payment_failed":
            invoice = event["data"]["object"]
            return StripeService._handle_payment_failed(invoice, db)

        return {"status": "success", "message": "Event processed"}

    @staticmethod
    def _handle_checkout_completed(session: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle successful checkout."""
        user_id = int(session["metadata"]["user_id"])
        plan = session["metadata"]["plan"]

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}

        # Update subscription
        subscription = user.subscription
        if not subscription:
            subscription = Subscription(user_id=user_id)
            db.add(subscription)

        subscription.plan = plan
        subscription.status = "active"
        subscription.stripe_customer_id = session["customer"]
        subscription.stripe_subscription_id = session["subscription"]

        # Get subscription details from Stripe
        stripe_sub = stripe.Subscription.retrieve(session["subscription"])
        subscription.current_period_start = datetime.fromtimestamp(stripe_sub["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(stripe_sub["current_period_end"])

        db.commit()

        return {"status": "success", "user_id": user_id, "plan": plan}

    @staticmethod
    def _handle_subscription_updated(subscription_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle subscription update."""
        stripe_sub_id = subscription_data["id"]

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub_id
        ).first()

        if not subscription:
            return {"status": "error", "message": "Subscription not found"}

        subscription.status = subscription_data["status"]
        subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
        subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

        db.commit()

        return {"status": "success"}

    @staticmethod
    def _handle_subscription_deleted(subscription_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        stripe_sub_id = subscription_data["id"]

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub_id
        ).first()

        if not subscription:
            return {"status": "error", "message": "Subscription not found"}

        # Downgrade to free plan
        subscription.plan = "free"
        subscription.status = "canceled"

        db.commit()

        return {"status": "success"}

    @staticmethod
    def _handle_payment_failed(invoice_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Handle failed payment."""
        stripe_sub_id = invoice_data["subscription"]

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub_id
        ).first()

        if not subscription:
            return {"status": "error", "message": "Subscription not found"}

        subscription.status = "past_due"

        db.commit()

        return {"status": "success"}

    @staticmethod
    def cancel_subscription(user: User, db: Session) -> Dict[str, Any]:
        """
        Cancel a user's subscription.

        Args:
            user: User object
            db: Database session

        Returns:
            dict: Cancellation result
        """
        subscription = user.subscription

        if not subscription or not subscription.stripe_subscription_id:
            return {"status": "error", "message": "No active subscription"}

        # Cancel in Stripe
        stripe.Subscription.delete(subscription.stripe_subscription_id)

        # Update local subscription
        subscription.plan = "free"
        subscription.status = "canceled"

        db.commit()

        return {"status": "success", "message": "Subscription canceled"}

    @staticmethod
    def get_usage_limits(plan: str) -> Dict[str, int]:
        """
        Get usage limits for a plan.

        Args:
            plan: Plan name

        Returns:
            dict: Usage limits
        """
        plan_data = StripeService.PLANS.get(plan, StripeService.PLANS["free"])

        return {
            "papers_per_day": plan_data["papers_per_day"],
            "experiments_per_week": plan_data["experiments_per_week"],
        }
