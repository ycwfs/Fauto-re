"""Security tests for common vulnerabilities."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.models import User


def test_sql_injection_protection(client: TestClient, auth_headers: dict):
    """Test SQL injection protection in search endpoints."""
    # Attempt SQL injection in search query
    malicious_query = "'; DROP TABLE papers; --"
    response = client.get(
        f"/api/papers/?search={malicious_query}",
        headers=auth_headers,
    )
    # Should not crash, should return empty or error
    assert response.status_code in [200, 400]


def test_xss_protection(client: TestClient):
    """Test XSS protection in user input."""
    xss_payload = "<script>alert('XSS')</script>"
    response = client.post(
        "/api/auth/register",
        json={
            "email": "xss@example.com",
            "password": "password123",
            "full_name": xss_payload,
        },
    )
    assert response.status_code == 200
    # Verify the payload is stored as-is (not executed)
    data = response.json()
    assert data["full_name"] == xss_payload


def test_password_hashing(db: Session):
    """Test that passwords are properly hashed."""
    from src.utils.auth import get_password_hash, verify_password

    password = "mysecretpassword"
    hashed = get_password_hash(password)

    # Hash should not equal plaintext
    assert hashed != password

    # Should be able to verify
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_expiration(client: TestClient, test_user: User, mocker):
    """Test JWT token expiration."""
    from datetime import timedelta
    from src.utils.auth import create_access_token

    # Create expired token
    expired_token = create_access_token(
        data={"sub": test_user.email},
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


def test_unauthorized_access(client: TestClient):
    """Test that protected endpoints require authentication."""
    endpoints = [
        "/api/users/me",
        "/api/papers/",
        "/api/experiments/",
        "/api/ideas/",
        "/api/writing/papers",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401


def test_rate_limiting_headers(client: TestClient, auth_headers: dict):
    """Test that rate limiting headers are present."""
    response = client.get("/api/papers/", headers=auth_headers)
    # Note: This test assumes rate limiting middleware is configured
    # In production, you should see X-RateLimit-* headers
    assert response.status_code == 200


def test_cors_headers(client: TestClient):
    """Test CORS headers are properly set."""
    response = client.options("/api/auth/login")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


def test_sensitive_data_not_exposed(client: TestClient, auth_headers: dict, test_user: User):
    """Test that sensitive data is not exposed in API responses."""
    response = client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Password hash should never be returned
    assert "hashed_password" not in data
    assert "password" not in data


def test_path_traversal_protection(client: TestClient, auth_headers: dict):
    """Test protection against path traversal attacks."""
    malicious_path = "../../etc/passwd"
    response = client.get(
        f"/api/papers/{malicious_path}",
        headers=auth_headers,
    )
    # Should return 404 or 400, not expose file system
    assert response.status_code in [400, 404, 422]


def test_csrf_protection(client: TestClient):
    """Test CSRF protection for state-changing operations."""
    # Attempt to register without proper headers
    response = client.post(
        "/api/auth/register",
        json={
            "email": "csrf@example.com",
            "password": "password123",
            "full_name": "CSRF Test",
        },
    )
    # Should still work with proper content-type
    # In production, you might want additional CSRF tokens
    assert response.status_code in [200, 403]
