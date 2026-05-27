"""Tests for experiments API endpoints."""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models.models import User, Experiment


@pytest.fixture
def sample_experiment(db: Session, test_user: User):
    """Create a sample experiment."""
    experiment = Experiment(
        user_id=test_user.id,
        name="Test Experiment",
        description="Testing autonomous experiment",
        base_repo_url="https://github.com/test/repo",
        status="pending",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def test_create_experiment(client: TestClient, auth_headers: dict):
    """Test creating a new experiment."""
    response = client.post(
        "/api/experiments/",
        headers=auth_headers,
        json={
            "name": "New Experiment",
            "description": "Test description",
            "base_repo_url": "https://github.com/test/repo",
            "goals": "Improve model accuracy",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Experiment"
    assert data["status"] == "pending"
    assert "id" in data


def test_list_experiments(client: TestClient, auth_headers: dict, sample_experiment):
    """Test listing experiments."""
    response = client.get("/api/experiments/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Experiment"


def test_get_experiment(client: TestClient, auth_headers: dict, sample_experiment):
    """Test getting a specific experiment."""
    response = client.get(
        f"/api/experiments/{sample_experiment.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_experiment.id
    assert data["name"] == "Test Experiment"


def test_start_experiment(client: TestClient, auth_headers: dict, sample_experiment, mocker):
    """Test starting an experiment."""
    mock_task = mocker.patch("src.api.experiments.setup_experiment.delay")
    mock_task.return_value.id = "setup-task-id"

    response = client.post(
        f"/api/experiments/{sample_experiment.id}/start", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "setting_up"
    mock_task.assert_called_once()


def test_stop_experiment(client: TestClient, auth_headers: dict, sample_experiment, db: Session, mocker):
    """Test stopping an experiment."""
    # Set experiment to running
    sample_experiment.status = "running"
    db.commit()

    mock_task = mocker.patch("src.api.experiments.stop_experiment.delay")

    response = client.post(
        f"/api/experiments/{sample_experiment.id}/stop", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopping"
    mock_task.assert_called_once()


def test_get_experiment_status(client: TestClient, auth_headers: dict, sample_experiment):
    """Test getting experiment status."""
    response = client.get(
        f"/api/experiments/{sample_experiment.id}/status", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "results" in data


def test_delete_experiment(client: TestClient, auth_headers: dict, sample_experiment):
    """Test deleting an experiment."""
    response = client.delete(
        f"/api/experiments/{sample_experiment.id}", headers=auth_headers
    )
    assert response.status_code == 200

    # Verify deletion
    response = client.get(
        f"/api/experiments/{sample_experiment.id}", headers=auth_headers
    )
    assert response.status_code == 404
