"""
Celery tasks for experiment management.
"""
from src.celery_app import celery_app
from src.database import SessionLocal
from src.services.experiment_runner import UserExperimentRunner
from src.models import Experiment
from datetime import datetime


@celery_app.task(name="setup_experiment")
def setup_experiment(user_id: int, experiment_id: int, idea_description: str, base_repo: str = None) -> dict:
    """
    Background task to set up an experiment environment.

    Args:
        user_id: User ID
        experiment_id: Experiment ID
        idea_description: Research idea description
        base_repo: Optional base repository URL

    Returns:
        dict: Setup result
    """
    db = SessionLocal()
    try:
        runner = UserExperimentRunner(user_id, experiment_id, db)
        result = runner.setup_experiment(idea_description, base_repo)

        if result["status"] == "success":
            # Update experiment status
            experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
            if experiment:
                experiment.status = "pending"
                db.commit()

        return result

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "user_id": user_id,
            "experiment_id": experiment_id,
            "message": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="run_autonomous_experiment")
def run_autonomous_experiment(user_id: int, experiment_id: int, max_iterations: int = 100) -> dict:
    """
    Background task to run autonomous experiment loop.

    Args:
        user_id: User ID
        experiment_id: Experiment ID
        max_iterations: Maximum number of iterations (default: 100)

    Returns:
        dict: Experiment result
    """
    db = SessionLocal()
    try:
        runner = UserExperimentRunner(user_id, experiment_id, db)

        # Update status to running
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not experiment:
            return {"status": "error", "message": "Experiment not found"}

        experiment.status = "running"
        experiment.started_at = datetime.utcnow()
        db.commit()

        # Run experiment iterations
        iterations_completed = 0
        for i in range(max_iterations):
            result = runner.run_experiment_iteration()

            if result["status"] == "failed" or result["status"] == "error":
                # Stop on failure
                experiment.status = "failed"
                db.commit()
                return {
                    "status": "failed",
                    "iterations_completed": iterations_completed,
                    "error": result.get("message"),
                }

            iterations_completed += 1

            # Check if we should continue
            if result["status"] == "timeout":
                break

        # Mark as completed
        experiment.status = "completed"
        experiment.completed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "user_id": user_id,
            "experiment_id": experiment_id,
            "iterations_completed": iterations_completed,
            "best_val_bpb": experiment.best_val_bpb,
        }

    except Exception as e:
        db.rollback()
        # Mark experiment as failed
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if experiment:
            experiment.status = "failed"
            db.commit()

        return {
            "status": "error",
            "user_id": user_id,
            "experiment_id": experiment_id,
            "message": str(e),
        }
    finally:
        db.close()


@celery_app.task(name="stop_experiment")
def stop_experiment(user_id: int, experiment_id: int) -> dict:
    """
    Background task to stop a running experiment.

    Args:
        user_id: User ID
        experiment_id: Experiment ID

    Returns:
        dict: Stop result
    """
    db = SessionLocal()
    try:
        runner = UserExperimentRunner(user_id, experiment_id, db)
        result = runner.stop_experiment()
        return result

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "user_id": user_id,
            "experiment_id": experiment_id,
            "message": str(e),
        }
    finally:
        db.close()
