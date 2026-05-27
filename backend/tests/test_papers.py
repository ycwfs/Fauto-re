"""Tests for papers API endpoints."""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.models import User, Paper


@pytest.fixture
def sample_papers(db: Session, test_user: User):
    """Create sample papers for testing."""
    papers = []
    for i in range(5):
        paper = Paper(
            user_id=test_user.id,
            arxiv_id=f"2024.{i:05d}",
            title=f"Test Paper {i}",
            authors=f"Author {i}",
            abstract=f"Abstract for paper {i}",
            categories="cs.AI",
            published_date=datetime(2024, 1, i + 1),
            pdf_url=f"https://arxiv.org/pdf/2024.{i:05d}.pdf",
        )
        db.add(paper)
        papers.append(paper)
    db.commit()
    return papers


def test_list_papers(client: TestClient, auth_headers: dict, sample_papers):
    """Test listing papers with pagination."""
    response = client.get("/api/papers/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["size"] == 50


def test_list_papers_pagination(client: TestClient, auth_headers: dict, sample_papers):
    """Test papers pagination."""
    response = client.get("/api/papers/?page=1&size=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 2


def test_get_paper(client: TestClient, auth_headers: dict, sample_papers):
    """Test getting a specific paper."""
    paper_id = sample_papers[0].id
    response = client.get(f"/api/papers/{paper_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == paper_id
    assert data["title"] == "Test Paper 0"


def test_get_nonexistent_paper(client: TestClient, auth_headers: dict):
    """Test getting a nonexistent paper."""
    response = client.get("/api/papers/99999", headers=auth_headers)
    assert response.status_code == 404


def test_get_papers_stats(client: TestClient, auth_headers: dict, sample_papers):
    """Test getting paper statistics."""
    response = client.get("/api/papers/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_papers"] == 5
    assert data["papers_this_week"] >= 0
    assert data["papers_this_month"] >= 0


def test_trigger_fetch_papers(client: TestClient, auth_headers: dict, mocker):
    """Test triggering paper fetch."""
    # Mock Celery task
    mock_task = mocker.patch("src.api.papers.fetch_papers_for_user.delay")
    mock_task.return_value.id = "test-task-id"

    response = client.post("/api/papers/fetch", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert data["task_id"] == "test-task-id"
    mock_task.assert_called_once()


def test_list_papers_unauthorized(client: TestClient):
    """Test listing papers without authentication."""
    response = client.get("/api/papers/")
    assert response.status_code == 401
