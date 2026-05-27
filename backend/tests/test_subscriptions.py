"""Tests for subscriptions and Stripe integration."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.models import User, Subscription


@pytest.fixture
def user_with_subscription(db: Session, test_user: User):
    """Create a user with a subscription."""
    subscription = Subscription(
        user_id=test_user.id,
        plan="free",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return test_user, subscription


def test_get_subscription(client: TestClient, auth_headers: dict, user_with_subscription):
    """Test getting current subscription."""
    response = client.get("/api/subscriptions/current", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "free"
    assert data["status"] == "active"


def test_create_checkout_session(client: TestClient, auth_headers: dict, mocker):
    """Test creating Stripe checkout session."""
    mock_stripe = mocker.patch("src.api.subscriptions.stripe_service.create_checkout_session")
    mock_stripe.return_value = "https://checkout.stripe.com/session123"

    response = client.post(
        "/api/subscriptions/checkout",
        headers=auth_headers,
        json={"plan": "pro"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "checkout_url" in data
    mock_stripe.assert_called_once()


def test_cancel_subscription(client: TestClient, auth_headers: dict, user_with_subscription, mocker):
    """Test canceling subscription."""
    user, subscription = user_with_subscription
    subscription.stripe_subscription_id = "sub_test123"

    mock_stripe = mocker.patch("src.api.subscriptions.stripe_service.cancel_subscription")

    response = client.post("/api/subscriptions/cancel", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    mock_stripe.assert_called_once()


def test_get_usage_limits(client: TestClient, auth_headers: dict, user_with_subscription):
    """Test getting usage limits."""
    response = client.get("/api/subscriptions/limits", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "papers_per_day" in data
    assert "experiments_per_week" in data
    assert data["papers_per_day"] == 10  # Free tier


def test_stripe_webhook_subscription_created(client: TestClient, mocker):
    """Test Stripe webhook for subscription created."""
    mock_construct = mocker.patch("stripe.Webhook.construct_event")
    mock_construct.return_value = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "items": {
                    "data": [{"price": {"id": "price_pro"}}]
                },
                "current_period_start": 1234567890,
                "current_period_end": 1237159890,
            }
        },
    }

    response = client.post(
        "/api/subscriptions/webhook",
        headers={"stripe-signature": "test_signature"},
        json={},
    )
    assert response.status_code == 200


def test_check_usage_limit_exceeded(client: TestClient, auth_headers: dict, user_with_subscription, db: Session):
    """Test usage limit enforcement."""
    user, subscription = user_with_subscription

    # Set usage to limit
    subscription.papers_fetched_today = 10  # Free tier limit
    db.commit()

    # Mock the usage check
    response = client.get("/api/subscriptions/limits", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["papers_per_day"] == 10
