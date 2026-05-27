"""End-to-end tests for complete workflows."""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.models import User, Paper, Idea, Experiment, WrittenPaper


def test_complete_research_workflow(client: TestClient, auth_headers: dict, db: Session, test_user: User, mocker):
    """Test complete workflow: Paper Discovery → Ideas → Experiments → Paper Writing."""

    # Stage 1: Paper Discovery
    # Mock paper fetching task
    mock_fetch = mocker.patch("src.api.papers.fetch_papers_for_user.delay")
    mock_fetch.return_value.id = "fetch-task-id"

    response = client.post("/api/papers/fetch", headers=auth_headers)
    assert response.status_code == 200

    # Simulate papers being fetched
    paper = Paper(
        user_id=test_user.id,
        arxiv_id="2024.12345",
        title="Novel Approach to AI Research",
        authors="Test Author",
        abstract="This paper presents a novel approach...",
        categories="cs.AI",
        published_date=datetime.utcnow(),
        pdf_url="https://arxiv.org/pdf/2024.12345.pdf",
    )
    db.add(paper)
    db.commit()

    # Verify papers are listed
    response = client.get("/api/papers/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1

    # Stage 2: Research Ideas
    # Create a research idea
    response = client.post(
        "/api/ideas/",
        headers=auth_headers,
        json={
            "title": "Improve Model Efficiency",
            "description": "Based on recent papers, we can improve efficiency by...",
            "keywords": ["efficiency", "optimization"],
        },
    )
    assert response.status_code == 200
    idea_id = response.json()["id"]

    # Approve the idea
    response = client.post(f"/api/ideas/{idea_id}/approve", headers=auth_headers)
    assert response.status_code == 200

    # Stage 3: Experiments
    # Create experiment from idea
    mock_setup = mocker.patch("src.api.experiments.setup_experiment.delay")
    mock_setup.return_value.id = "setup-task-id"

    response = client.post(
        "/api/experiments/",
        headers=auth_headers,
        json={
            "name": "Efficiency Experiment",
            "description": "Testing efficiency improvements",
            "base_repo_url": "https://github.com/test/repo",
            "goals": "Improve model efficiency by 20%",
            "idea_id": idea_id,
        },
    )
    assert response.status_code == 200
    experiment_id = response.json()["id"]

    # Start experiment
    response = client.post(f"/api/experiments/{experiment_id}/start", headers=auth_headers)
    assert response.status_code == 200

    # Check experiment status
    response = client.get(f"/api/experiments/{experiment_id}/status", headers=auth_headers)
    assert response.status_code == 200

    # Stage 4: Paper Writing
    # Mock paper writing
    mock_outline = mocker.patch("src.api.writing.paper_writer.generate_outline")
    mock_outline.return_value = {
        "title": "Efficient AI Models",
        "sections": ["Introduction", "Method", "Experiments", "Conclusion"],
    }

    response = client.post(
        "/api/writing/papers",
        headers=auth_headers,
        json={
            "experiment_id": experiment_id,
            "venue": "NeurIPS",
            "title": "Efficient AI Models",
        },
    )
    assert response.status_code == 200
    paper_id = response.json()["id"]

    # Generate outline
    response = client.post(
        f"/api/writing/papers/{paper_id}/outline",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Verify complete workflow
    assert db.query(Paper).filter(Paper.user_id == test_user.id).count() >= 1
    assert db.query(Idea).filter(Idea.user_id == test_user.id).count() >= 1
    assert db.query(Experiment).filter(Experiment.user_id == test_user.id).count() >= 1
    assert db.query(WrittenPaper).filter(WrittenPaper.user_id == test_user.id).count() >= 1


def test_multi_user_isolation(client: TestClient, db: Session):
    """Test that users can only access their own data."""
    # Create two users
    from src.utils.auth import get_password_hash

    user1 = User(
        email="user1@example.com",
        hashed_password=get_password_hash("password1"),
        full_name="User One",
    )
    user2 = User(
        email="user2@example.com",
        hashed_password=get_password_hash("password2"),
        full_name="User Two",
    )
    db.add_all([user1, user2])
    db.commit()

    # Create paper for user1
    paper = Paper(
        user_id=user1.id,
        arxiv_id="2024.11111",
        title="User 1 Paper",
        authors="Author 1",
        abstract="Abstract 1",
        categories="cs.AI",
        published_date=datetime.utcnow(),
        pdf_url="https://arxiv.org/pdf/2024.11111.pdf",
    )
    db.add(paper)
    db.commit()

    # Login as user2
    response = client.post(
        "/api/auth/login",
        data={"username": "user2@example.com", "password": "password2"},
    )
    user2_token = response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # User2 should not see user1's papers
    response = client.get("/api/papers/", headers=user2_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0

    # User2 should not be able to access user1's paper directly
    response = client.get(f"/api/papers/{paper.id}", headers=user2_headers)
    assert response.status_code == 404
