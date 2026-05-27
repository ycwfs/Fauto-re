from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.database import get_db
from src.models import User, Idea
from src.api.dependencies import get_current_active_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class IdeaCreate(BaseModel):
    """Schema for creating an idea."""

    title: str
    description: Optional[str] = None
    motivation: Optional[str] = None
    approach: Optional[str] = None
    expected_outcomes: Optional[str] = None
    source_paper_ids: Optional[List[int]] = None


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""

    title: Optional[str] = None
    description: Optional[str] = None
    motivation: Optional[str] = None
    approach: Optional[str] = None
    expected_outcomes: Optional[str] = None
    status: Optional[str] = None


class IdeaResponse(BaseModel):
    """Schema for idea response."""

    id: int
    title: str
    description: Optional[str]
    motivation: Optional[str]
    approach: Optional[str]
    expected_outcomes: Optional[str]
    status: str
    generated_at: datetime
    approved_at: Optional[datetime]

    class Config:
        from_attributes = True


class IdeaListResponse(BaseModel):
    """Schema for paginated idea list response."""

    ideas: List[IdeaResponse]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    idea_data: IdeaCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new research idea."""
    idea = Idea(
        user_id=current_user.id,
        title=idea_data.title,
        description=idea_data.description,
        motivation=idea_data.motivation,
        approach=idea_data.approach,
        expected_outcomes=idea_data.expected_outcomes,
        source_paper_ids=idea_data.source_paper_ids or [],
        status="pending",
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)

    return idea


@router.get("/", response_model=IdeaListResponse)
async def list_ideas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List research ideas for the current user with pagination."""
    query = db.query(Idea).filter(Idea.user_id == current_user.id)

    # Filter by status if provided
    if status_filter:
        query = query.filter(Idea.status == status_filter)

    # Get total count
    total = query.count()

    # Paginate
    ideas = (
        query.order_by(desc(Idea.generated_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "ideas": ideas,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific idea by ID."""
    idea = db.query(Idea).filter(
        Idea.id == idea_id,
        Idea.user_id == current_user.id
    ).first()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    return idea


@router.put("/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: int,
    idea_data: IdeaUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update an idea."""
    idea = db.query(Idea).filter(
        Idea.id == idea_id,
        Idea.user_id == current_user.id
    ).first()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    # Update only provided fields
    update_data = idea_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(idea, field, value)

    # Set approved_at if status changed to approved
    if idea_data.status == "approved" and idea.approved_at is None:
        idea.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(idea)

    return idea


@router.post("/{idea_id}/approve", response_model=IdeaResponse)
async def approve_idea(
    idea_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Approve an idea for experimentation."""
    idea = db.query(Idea).filter(
        Idea.id == idea_id,
        Idea.user_id == current_user.id
    ).first()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    idea.status = "approved"
    idea.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(idea)

    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an idea."""
    idea = db.query(Idea).filter(
        Idea.id == idea_id,
        Idea.user_id == current_user.id
    ).first()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found",
        )

    db.delete(idea)
    db.commit()

    return None
