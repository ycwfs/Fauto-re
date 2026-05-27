"""
Experiment service - integrates autoresearch framework for multi-user.
"""
import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Add Auto-Research to path
AUTO_RESEARCH_PATH = Path("/data1/data1/wfs/misc/Auto-Research")
AUTORESEARCH_PATH = Path("/data1/data1/wfs/misc/Full-Auto-Reasearch/autoresearch")
sys.path.insert(0, str(AUTO_RESEARCH_PATH))

from src.utils.user_data import get_user_experiments_dir
from src.models import Experiment, Idea


class UserExperimentRunner:
    """Runs autonomous experiments for a specific user."""

    def __init__(self, user_id: int, experiment_id: int, db: Session):
        self.user_id = user_id
        self.experiment_id = experiment_id
        self.db = db
        self.experiments_dir = get_user_experiments_dir(user_id)
        self.experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()

    def setup_experiment(self, idea_description: str, base_repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Set up a new experiment environment.

        Args:
            idea_description: Description of the research idea
            base_repo: Optional base repository to start from

        Returns:
            dict: Setup result with branch name and paths
        """
        if not self.experiment:
            return {"status": "error", "message": "Experiment not found"}

        # Create experiment directory
        exp_dir = self.experiments_dir / f"exp_{self.experiment_id}"
        exp_dir.mkdir(parents=True, exist_ok=True)

        # Copy autoresearch template
        if base_repo:
            # Clone base repo
            subprocess.run(
                ["git", "clone", base_repo, str(exp_dir)],
                check=True,
                capture_output=True,
            )
        else:
            # Copy autoresearch template
            subprocess.run(
                ["cp", "-r", str(AUTORESEARCH_PATH), str(exp_dir)],
                check=True,
            )

        # Create experiment branch
        branch_name = f"autoresearch/exp_{self.experiment_id}_{datetime.now().strftime('%Y%m%d')}"

        os.chdir(exp_dir)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        # Initialize results.tsv
        results_file = exp_dir / "results.tsv"
        with open(results_file, "w") as f:
            f.write("commit\tval_bpb\tmemory_gb\tstatus\tdescription\n")

        # Create custom program.md with idea
        program_file = exp_dir / "program.md"
        program_content = f"""# Experiment: {self.experiment.name}

## Research Idea
{idea_description}

## Goal
Implement and validate this research idea through autonomous experimentation.

## Instructions
Follow the standard autoresearch workflow:
1. Modify train.py to implement the idea
2. Run training for 5 minutes
3. Evaluate val_bpb
4. Keep if improved, discard otherwise
5. Iterate continuously

Focus on achieving the lowest val_bpb while implementing the core idea.
"""
        with open(program_file, "w") as f:
            f.write(program_content)

        # Update experiment in database
        self.experiment.branch_name = branch_name
        self.experiment.status = "pending"
        self.experiment.results_tsv_path = str(results_file)
        self.db.commit()

        return {
            "status": "success",
            "experiment_id": self.experiment_id,
            "branch_name": branch_name,
            "experiment_dir": str(exp_dir),
            "results_file": str(results_file),
        }

    def run_experiment_iteration(self) -> Dict[str, Any]:
        """
        Run a single experiment iteration.

        Returns:
            dict: Iteration result with val_bpb and status
        """
        if not self.experiment:
            return {"status": "error", "message": "Experiment not found"}

        exp_dir = self.experiments_dir / f"exp_{self.experiment_id}"

        if not exp_dir.exists():
            return {"status": "error", "message": "Experiment directory not found"}

        os.chdir(exp_dir)

        # Run training
        try:
            result = subprocess.run(
                ["uv", "run", "train.py"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes max
            )

            # Parse results
            output = result.stdout
            val_bpb = None
            peak_vram_mb = None

            for line in output.split("\n"):
                if line.startswith("val_bpb:"):
                    val_bpb = float(line.split(":")[1].strip())
                elif line.startswith("peak_vram_mb:"):
                    peak_vram_mb = float(line.split(":")[1].strip())

            if val_bpb is None:
                # Training failed
                return {
                    "status": "failed",
                    "message": "Training crashed or produced no output",
                    "output": output[-1000:],  # Last 1000 chars
                }

            # Update experiment stats
            if self.experiment.best_val_bpb is None or val_bpb < self.experiment.best_val_bpb:
                self.experiment.best_val_bpb = val_bpb

            self.experiment.total_runs += 1
            self.db.commit()

            return {
                "status": "success",
                "val_bpb": val_bpb,
                "peak_vram_mb": peak_vram_mb,
                "improved": val_bpb < (self.experiment.best_val_bpb or float("inf")),
            }

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Training exceeded time limit"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_experiment_status(self) -> Dict[str, Any]:
        """Get current experiment status and results."""
        if not self.experiment:
            return {"status": "error", "message": "Experiment not found"}

        results_file = Path(self.experiment.results_tsv_path) if self.experiment.results_tsv_path else None

        results = []
        if results_file and results_file.exists():
            with open(results_file, "r") as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    parts = line.strip().split("\t")
                    if len(parts) >= 5:
                        results.append({
                            "commit": parts[0],
                            "val_bpb": float(parts[1]) if parts[1] != "0.000000" else None,
                            "memory_gb": float(parts[2]),
                            "status": parts[3],
                            "description": parts[4],
                        })

        return {
            "experiment_id": self.experiment.id,
            "name": self.experiment.name,
            "status": self.experiment.status,
            "best_val_bpb": self.experiment.best_val_bpb,
            "total_runs": self.experiment.total_runs,
            "results": results,
            "started_at": self.experiment.started_at.isoformat() if self.experiment.started_at else None,
            "completed_at": self.experiment.completed_at.isoformat() if self.experiment.completed_at else None,
        }

    def stop_experiment(self) -> Dict[str, Any]:
        """Stop the experiment and mark as completed."""
        if not self.experiment:
            return {"status": "error", "message": "Experiment not found"}

        self.experiment.status = "completed"
        self.experiment.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "status": "success",
            "experiment_id": self.experiment_id,
            "final_best_val_bpb": self.experiment.best_val_bpb,
            "total_runs": self.experiment.total_runs,
        }
