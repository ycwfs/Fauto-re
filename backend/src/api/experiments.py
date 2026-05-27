from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.database import get_db
from src.models import User, Experiment, Idea
from src.api.dependencies import get_current_active_user
from src.services.experiment_tasks import setup_experiment, run_autonomous_experiment, stop_experiment
from src.services.experiment_runner import UserExperimentRunner
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class ExperimentCreate(BaseModel):
    """Schema for creating an experiment."""

    name: str
    description: Optional[str] = None
    idea_id: Optional[int] = None
    idea_description: str
    base_repo: Optional[str] = None
    max_iterations: int = 100


class ExperimentResponse(BaseModel):
    """Schema for experiment response."""

    id: int
    name: str
    description: Optional[str]
    status: str
    best_val_bpb: Optional[float]
    total_runs: int
    branch_name: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ExperimentListResponse(BaseModel):
    """Schema for paginated experiment list response."""

    experiments: List[ExperimentResponse]
    total: int
    page: int
    page_size: int


class ExperimentStatusResponse(BaseModel):
    """Schema for detailed experiment status."""

    experiment_id: int
    name: str
    status: str
    best_val_bpb: Optional[float]
    total_runs: int
    results: List[dict]
    started_at: Optional[str]
    completed_at: Optional[str]


@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    experiment_data: ExperimentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new experiment."""
    # Create experiment record
    experiment = Experiment(
        user_id=current_user.id,
        idea_id=experiment_data.idea_id,
        name=experiment_data.name,
        description=experiment_data.description,
        status="pending",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    # Queue setup task
    setup_experiment.delay(
        user_id=current_user.id,
        experiment_id=experiment.id,
        idea_description=experiment_data.idea_description,
        base_repo=experiment_data.base_repo,
    )

    return experiment


@router.get("/", response_model=ExperimentListResponse)
async def list_experiments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List experiments for the current user with pagination."""
    query = db.query(Experiment).filter(Experiment.user_id == current_user.id)

    # Filter by status if provided
    if status_filter:
        query = query.filter(Experiment.status == status_filter)

    # Get total count
    total = query.count()

    # Paginate
    experiments = (
        query.order_by(desc(Experiment.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "experiments": experiments,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific experiment by ID."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id,
        Experiment.user_id == current_user.id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    return experiment


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
async def get_experiment_status(
    experiment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get detailed experiment status with results."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id,
        Experiment.user_id == current_user.id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    runner = UserExperimentRunner(current_user.id, experiment_id, db)
    status_data = runner.get_experiment_status()

    return status_data


@router.post("/{experiment_id}/start", status_code=status.HTTP_202_ACCEPTED)
async def start_experiment(
    experiment_id: int,
    max_iterations: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Start running an experiment."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id,
        Experiment.user_id == current_user.id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    if experiment.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment is already running",
        )

    # Queue experiment task
    task = run_autonomous_experiment.delay(
        user_id=current_user.id,
        experiment_id=experiment_id,
        max_iterations=max_iterations,
    )

    return {
        "message": "Experiment started",
        "experiment_id": experiment_id,
        "task_id": task.id,
    }


@router.post("/{experiment_id}/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_experiment_endpoint(
    experiment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Stop a running experiment."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id,
        Experiment.user_id == current_user.id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    if experiment.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Experiment is not running",
        )

    # Queue stop task
    task = stop_experiment.delay(
        user_id=current_user.id,
        experiment_id=experiment_id,
    )

    return {
        "message": "Experiment stop requested",
        "experiment_id": experiment_id,
        "task_id": task.id,
    }


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    experiment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an experiment."""
    experiment = db.query(Experiment).filter(
        Experiment.id == experiment_id,
        Experiment.user_id == current_user.id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    if experiment.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running experiment",
        )

    db.delete(experiment)
    db.commit()

    return None
