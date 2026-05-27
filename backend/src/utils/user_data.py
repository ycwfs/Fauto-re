"""
User-specific data isolation utilities.

Provides functions to get per-user data paths and ensure proper isolation.
"""
import os
from pathlib import Path
from src.config import settings


def get_user_data_dir(user_id: int) -> Path:
    """Get the base data directory for a user."""
    user_dir = Path(settings.user_data_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_papers_dir(user_id: int) -> Path:
    """Get the papers directory for a user."""
    papers_dir = get_user_data_dir(user_id) / "papers"
    papers_dir.mkdir(exist_ok=True)
    return papers_dir


def get_user_summaries_dir(user_id: int) -> Path:
    """Get the summaries directory for a user."""
    summaries_dir = get_user_data_dir(user_id) / "summaries"
    summaries_dir.mkdir(exist_ok=True)
    return summaries_dir


def get_user_analyses_dir(user_id: int) -> Path:
    """Get the analyses directory for a user."""
    analyses_dir = get_user_data_dir(user_id) / "analyses"
    analyses_dir.mkdir(exist_ok=True)
    return analyses_dir


def get_user_experiments_dir(user_id: int) -> Path:
    """Get the experiments directory for a user."""
    experiments_dir = get_user_data_dir(user_id) / "experiments"
    experiments_dir.mkdir(exist_ok=True)
    return experiments_dir


def get_user_fulltext_dir(user_id: int) -> Path:
    """Get the fulltext directory for a user."""
    fulltext_dir = get_user_data_dir(user_id) / "fulltext"
    fulltext_dir.mkdir(exist_ok=True)
    return fulltext_dir


def get_user_runtime_dir(user_id: int) -> Path:
    """Get the runtime directory for a user."""
    runtime_dir = get_user_data_dir(user_id) / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    return runtime_dir


def get_user_config_path(user_id: int) -> Path:
    """Get the config file path for a user."""
    config_path = get_user_data_dir(user_id) / "config.yaml"
    return config_path
