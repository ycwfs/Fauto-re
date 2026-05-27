from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models import User, UserPreference
from src.api.dependencies import get_current_active_user
from src.api.schemas import UserResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class UserPreferenceUpdate(BaseModel):
    """Schema for updating user preferences."""

    arxiv_categories: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    max_papers_per_day: Optional[int] = None
    daily_run_time: Optional[str] = None
    weekly_idea_day: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    notify_new_papers: Optional[bool] = None
    notify_new_ideas: Optional[bool] = None
    notify_experiment_complete: Optional[bool] = None


class UserPreferenceResponse(BaseModel):
    """Schema for user preferences response."""

    arxiv_categories: List[str]
    keywords: List[str]
    max_papers_per_day: int
    daily_run_time: str
    weekly_idea_day: str
    timezone: str
    email_notifications: bool
    notify_new_papers: bool
    notify_new_ideas: bool
    notify_experiment_complete: bool

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user information."""
    return current_user


@router.get("/me/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user preferences."""
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )

    return preferences


@router.put("/me/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    preference_data: UserPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user preferences."""
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == current_user.id
    ).first()

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )

    # Update only provided fields
    update_data = preference_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)

    db.commit()
    db.refresh(preferences)

    return preferences
